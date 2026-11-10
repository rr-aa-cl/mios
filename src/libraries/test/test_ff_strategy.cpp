#include <cmath>
#include <iostream>
#include <stdexcept>
#include <string>

#include "mios/strategies/ff_strategy.hpp"

namespace {

using Wrench = Eigen::Matrix<double, 6, 1>;
constexpr double kTolerance = 1.0e-12;

Eigen::Matrix3d quarter_turn_z() {
    Eigen::Matrix3d rotation;
    rotation << 0, -1, 0, 1, 0, 0, 0, 0, 1;
    return rotation;
}

mios::Percept make_percept(const Eigen::Matrix3d& ee_rotation,
                           const Eigen::Matrix3d& task_rotation) {
    mios::Percept percept;
    percept.proprioception.O_T_EE.setIdentity();
    percept.proprioception.O_T_EE.block<3, 3>(0, 0) = ee_rotation;
    percept.proprioception.T_T_EE.setIdentity();
    percept.proprioception.q.setZero();
    percept.controller.O_R_T = task_rotation;
    return percept;
}

struct Fixture {
    mios::Percept percept;
    mios::ControlParameters control;
    mios::Actuator command;
    mios::FFStrategy strategy;

    Fixture(const Eigen::Matrix3d& ee_rotation = Eigen::Matrix3d::Identity(),
            const Eigen::Matrix3d& task_rotation = Eigen::Matrix3d::Identity())
        : percept(make_percept(ee_rotation, task_rotation)),
          command(percept, control) {}
};

void expect_wrench(const Wrench& actual, const Wrench& expected,
                   const std::string& message) {
    if (!actual.allFinite() || (actual - expected).cwiseAbs().maxCoeff() > kTolerance) {
        throw std::runtime_error(message);
    }
}

void expect_slew(const Wrench& current, const Wrench& previous,
                 const Eigen::Vector2d& rate) {
    for (Eigen::Index i = 0; i < 6; ++i) {
        const double step = rate(i < 3 ? 0 : 1) * 0.001;
        if (!std::isfinite(current(i)) ||
            std::abs(current(i) - previous(i)) > step + kTolerance) {
            throw std::runtime_error("wrench exceeded its per-cycle slew bound");
        }
    }
}

void task_frame_is_unchanged() {
    Fixture f(quarter_turn_z(), quarter_turn_z().transpose());
    Wrench requested;
    requested << 0.024, -0.015, 0.004, 0.0024, -0.0015, 0.0004;
    const Eigen::Vector2d rate(10.0, 1.0);
    f.strategy.set_TF_F_ff(requested, rate);
    f.strategy.initialize(f.percept);
    f.strategy.get_next_command(f.command, f.percept);
    Wrench first;
    first << 0.01, -0.01, 0.004, 0.001, -0.001, 0.0004;
    expect_wrench(f.command.TF_F_ff, first, "default task-frame first ramp changed");
    for (int cycle = 0; cycle < 5; ++cycle) {
        const Wrench previous = f.command.TF_F_ff;
        f.strategy.get_next_command(f.command, f.percept);
        expect_slew(f.command.TF_F_ff, previous, rate);
    }
    expect_wrench(f.command.TF_F_ff, requested, "default task-frame target changed");
}

void ee_first_ramp_uses_rotated_components() {
    Fixture f(quarter_turn_z());
    Wrench requested;
    requested << 1.0, 0.0, -0.004, 0.2, 0.0, -0.0004;
    const Eigen::Vector2d rate(10.0, 1.0);
    f.strategy.set_TF_F_ff(requested, rate);
    f.strategy.set_frame(true);
    f.strategy.initialize(f.percept);
    f.strategy.get_next_command(f.command, f.percept);
    Wrench expected;
    expected << 0.0, 0.01, -0.004, 0.0, 0.001, -0.0004;
    expect_wrench(f.command.TF_F_ff, expected, "EE first ramp used an unrotated component");
    expect_slew(f.command.TF_F_ff, Wrench::Zero(), rate);
}

void ee_ramp_converges_and_tracks_orientation() {
    Fixture f(quarter_turn_z());
    Wrench requested;
    requested << 0.024, -0.015, 0.004, 0.0024, -0.0015, 0.0004;
    const Eigen::Vector2d rate(10.0, 1.0);
    f.strategy.set_TF_F_ff(requested, rate);
    f.strategy.set_frame(true);
    f.strategy.initialize(f.percept);
    Wrench previous = Wrench::Zero();
    for (int cycle = 0; cycle < 8; ++cycle) {
        f.strategy.get_next_command(f.command, f.percept);
        expect_slew(f.command.TF_F_ff, previous, rate);
        previous = f.command.TF_F_ff;
    }
    Wrench target;
    target << 0.015, 0.024, 0.004, 0.0015, 0.0024, 0.0004;
    expect_wrench(previous, target, "EE ramp did not settle at the rotated target");

    // A changed pose changes the target, while the limiter retains its last output.
    f.percept.proprioception.O_T_EE.block<3, 3>(0, 0) = quarter_turn_z().transpose();
    for (int cycle = 0; cycle < 8; ++cycle) {
        f.strategy.get_next_command(f.command, f.percept);
        expect_slew(f.command.TF_F_ff, previous, rate);
        previous = f.command.TF_F_ff;
    }
    target << -0.015, -0.024, 0.004, -0.0015, -0.0024, 0.0004;
    expect_wrench(previous, target, "EE ramp did not follow the changed orientation");
}

void ee_wrench_is_expressed_in_nonidentity_task_frame() {
    Eigen::Matrix3d ee_rotation;
    ee_rotation << 1, 0, 0, 0, 0, -1, 0, 1, 0;
    Fixture f(ee_rotation, quarter_turn_z());
    Wrench requested;
    requested << -0.3, 0.7, -0.2, -0.04, -0.05, 0.06;
    f.strategy.set_TF_F_ff(requested, Eigen::Vector2d(1000.0, 1000.0));
    f.strategy.set_frame(true);
    f.strategy.initialize(f.percept);
    f.strategy.get_next_command(f.command, f.percept);
    Wrench expected;
    expected << 0.2, 0.3, 0.7, -0.06, 0.04, -0.05;
    expect_wrench(f.command.TF_F_ff, expected, "EE wrench ignored the task-frame rotation");
    f.strategy.get_next_command(f.command, f.percept);
    expect_wrench(f.command.TF_F_ff, expected, "non-limited output did not hold its rotated target");
}

}  // namespace

int main() {
    const struct {
        const char* name;
        void (*run)();
    } tests[] = {
        {"task frame unchanged", task_frame_is_unchanged},
        {"EE first ramp", ee_first_ramp_uses_rotated_components},
        {"EE convergence and changed orientation", ee_ramp_converges_and_tracks_orientation},
        {"nonidentity task frame", ee_wrench_is_expressed_in_nonidentity_task_frame},
    };
    int failures = 0;
    for (const auto& test : tests) {
        try {
            test.run();
            std::cout << "PASS: " << test.name << '\n';
        } catch (const std::exception& error) {
            ++failures;
            std::cerr << "FAIL: " << test.name << ": " << error.what() << '\n';
        }
    }
    return failures == 0 ? 0 : 1;
}
