from definitions.definitions_base import *
from utils.ws_client import call_method
from xmlrpc.client import ServerProxy


class InsertionFactory(ProblemDefinitionFactory):
    def __init__(self, robot: str, cost_function: CostFunctionFactory, objects: dict):
        super().__init__(robot, "insertion", [("TaxInsertion", "insertion", "insertion")],
                         [("MoveToPoseJoint", "move", "move_joint")],
                         [("TaxExtraction", "extraction", "extraction"),
                          ("MoveToPoseJoint", "move", "move_joint")], [], cost_function, objects)

    def get_limits(self):
        limits = {
            "p0_offset_x": (-0.005, 0.005),
            "p0_offset_y": (-0.005, 0.005),
            "p0_offset_phi": (-10, 10),
            "p0_offset_chi": (-10, 10),
            "p1_dx_d": (0, 0.1),
            "p1_dphi_d": (0, 0.5),
            "p1_ddx_d": (0, 0.5),
            "p1_ddphi_d": (0, 1),
            "p1_K_x": (0, 2000),
            "p1_K_phi": (0, 2000),
            "p2_dx_d": (0, 0.1),
            "p2_dphi_d": (0, 0.5),
            "p2_ddx_d": (0, 0.5),
            "p2_ddphi_d": (0, 1),
            "p2_wiggle_a_x": (0, 10),
            "p2_wiggle_a_y": (0, 10),
            # "p2_wiggle_a_z": (0, 10),
            "p2_wiggle_a_phi": (0, 2),
            "p2_wiggle_a_chi": (0, 2),
            "p2_wiggle_f_x": (0, 3),
            "p2_wiggle_f_y": (0, 3),
            # "p2_wiggle_f_z": (0, 3),
            "p2_wiggle_f_phi": (0, 1),
            "p2_wiggle_f_chi": (0, 1),
            "p2_wiggle_phi_x": (0, 6.28),
            "p2_wiggle_phi_y": (0, 6.28),
            # "p2_wiggle_phi_z": (0, 6.28),
            "p2_wiggle_phi_phi": (0, 6.28),
            "p2_wiggle_phi_chi": (0, 6.28),
            "p2_K_x": (0, 2000),
            "p2_K_y": (0, 2000),
            "p2_K_z": (0, 2000),
            "p2_K_phi": (0, 200),
            "p2_K_chi": (0, 200),
            "p2_K_psi": (0, 200),
            "p2_f_push_x": (-10, 10),
            "p2_f_push_y": (-10, 10),
            "p2_f_push_z": (0, 15)
        }
        return limits

    def get_mapping(self):
        context_mapping = {
            "p0_offset_x": ["skills.insertion.skill.p0.DeltaX-1"],
            "p0_offset_y": ["skills.insertion.skill.p0.DeltaX-2"],
            "p0_offset_phi": ["skills.insertion.skill.p0.DeltaX-4"],
            "p0_offset_chi": ["skills.insertion.skill.p0.DeltaX-5"],
            "p1_dx_d": ["skills.insertion.skill.p1.dX_d-1"],
            "p1_dphi_d": ["skills.insertion.skill.p1.dX_d-2"],
            "p1_ddx_d": ["skills.insertion.skill.p1.ddX_d-1"],
            "p1_ddphi_d": ["skills.insertion.skill.p1.ddX_d-2"],
            "p1_K_x": ["skills.insertion.skill.p1.K_x-1", "skills.insertion.skill.p1.K_x-2",
                       "skills.insertion.skill.p1.K_x-3"],
            "p1_K_phi": ["skills.insertion.skill.p1.K_x-4", "skills.insertion.skill.p1.K_x-5",
                         "skills.insertion.skill.p1.K_x-6"],
            "p2_dx_d": ["skills.insertion.skill.p2.dX_d-1"],
            "p2_dphi_d": ["skills.insertion.skill.p2.dX_d-2"],
            "p2_ddx_d": ["skills.insertion.skill.p2.ddX_d-1"],
            "p2_ddphi_d": ["skills.insertion.skill.p2.ddX_d-2"],
            "p2_wiggle_a_x": ["skills.insertion.skill.p2.search_a-1"],
            "p2_wiggle_a_y": ["skills.insertion.skill.p2.search_a-2"],
            # "p2_wiggle_a_z": ["skills.insertion.skill.p2.search_a-3"],
            "p2_wiggle_a_phi": ["skills.insertion.skill.p2.search_a-4"],
            "p2_wiggle_a_chi": ["skills.insertion.skill.p2.search_a-5"],
            "p2_wiggle_f_x": ["skills.insertion.skill.p2.search_f-1"],
            "p2_wiggle_f_y": ["skills.insertion.skill.p2.search_f-2"],
            # "p2_wiggle_f_z": ["skills.insertion.skill.p2.search_f-3"],
            "p2_wiggle_f_phi": ["skills.insertion.skill.p2.search_f-4"],
            "p2_wiggle_f_chi": ["skills.insertion.skill.p2.search_f-5"],
            "p2_wiggle_phi_x": ["skills.insertion.skill.p2.search_phi-1"],
            "p2_wiggle_phi_y": ["skills.insertion.skill.p2.search_phi-2"],
            # "p2_wiggle_phi_z": ["skills.insertion.skill.p2.search_phi-3"],
            "p2_wiggle_phi_phi": ["skills.insertion.skill.p2.search_phi-4"],
            "p2_wiggle_phi_chi": ["skills.insertion.skill.p2.search_phi-5"],
            "p2_K_x": ["skills.insertion.skill.p2.K_x-1"],
            "p2_K_y": ["skills.insertion.skill.p2.K_x-2"],
            "p2_K_z": ["skills.insertion.skill.p2.K_x-3"],
            "p2_K_phi": ["skills.insertion.skill.p2.K_x-4"],
            "p2_K_chi": ["skills.insertion.skill.p2.K_x-5"],
            "p2_K_psi": ["skills.insertion.skill.p2.K_x-6"],
            "p2_f_push_x": ["skills.insertion.skill.p2.f_push-1"],
            "p2_f_push_y": ["skills.insertion.skill.p2.f_push-2"],
            "p2_f_push_z": ["skills.insertion.skill.p2.f_push-3"]
        }
        return context_mapping

    def get_initial_values(self):
        x_0 = dict()
        for p in self.limits:
            x_0[p] = 0.1

        x_0["p0_offset_x"] = 0.5,
        x_0["p0_offset_y"] = 0.5,
        x_0["p0_offset_phi"] = 0.5,
        x_0["p0_offset_chi"] = 0.5,
        x_0["p2_f_push_x"] = 0.5,
        x_0["p2_f_push_y"] = 0.5,
        return x_0

    def ground_skills(self):
        print(self.setup_instructions)
        self.learn_context["skills"]["insertion"]["skill"]["objects"]["Approach"] = self.objects["Approach"]
        self.learn_context["skills"]["insertion"]["skill"]["objects"]["Container"] = self.objects["Container"]
        self.learn_context["skills"]["insertion"]["skill"]["objects"]["Insertable"] = self.objects["Insertable"]
        self.setup_instructions[0]["parameters"]["skills"]["move"]["skill"]["objects"]["goal_pose"] = self.objects[
            "Approach"]
        self.reset_instructions[0]["parameters"]["skills"]["extraction"]["skill"]["objects"]["ExtractTo"] = \
        self.objects["Approach"]
        self.reset_instructions[0]["parameters"]["skills"]["extraction"]["skill"]["objects"]["Container"] = \
        self.objects["Container"]
        self.reset_instructions[0]["parameters"]["skills"]["extraction"]["skill"]["objects"]["Extractable"] = \
        self.objects["Insertable"]
        self.reset_instructions[0]["parameters"]["skills"]["move"]["skill"]["objects"]["goal_pose"] = self.objects[
            "Approach"]

    def run_setup(self) -> bool:
        result = call_method(self.robot, 12000, "set_grasped_object", {"object": self.objects["Insertable"]})
        print(result)
        return True


class TipFactory(ProblemDefinitionFactory):
    def __init__(self, robot: str, cost_function: CostFunctionFactory, objects: dict):
        super().__init__(robot, "tip", [("TaxTip", "tip", "tip")],
                         [("MoveToPoseJoint", "move", "move_joint")],
                         [("MoveToPoseJoint", "move", "move_joint")], [], cost_function, objects)

    def get_limits(self):
        limits = {
            "p1_dx_d": (0, 0.1),
            "p1_dphi_d": (0, 0.5),
            "p1_ddx_d": (0, 0.5),
            "p1_ddphi_d": (0, 1),
            "p1_K_x": (0, 2000),
            "p1_K_phi": (0, 200),
            "p1_f_tip": (0, 20),
            "p2_dx_d": (0, 0.1),
            "p2_dphi_d": (0, 0.5),
            "p2_ddx_d": (0, 0.5),
            "p2_ddphi_d": (0, 1),
            "p2_K_x": (0, 2000),
            "p2_K_phi": (0, 200)
        }
        return limits

    def get_mapping(self):
        context_mapping = {
            "p1_dx_d": ["skills.tip.skill.p1.dX_d-1"],
            "p1_dphi_d": ["skills.tip.skill.p1.dX_d-2"],
            "p1_ddx_d": ["skills.tip.skill.p1.ddX_d-1"],
            "p1_ddphi_d": ["skills.tip.skill.p1.ddX_d-2"],
            "p1_K_x": ["skills.tip.skill.p1.K_x-1", "skills.tip.skill.p1.K_x-2",
                       "skills.tip.skill.p1.K_x-3"],
            "p1_K_phi": ["skills.tip.skill.p1.K_x-4", "skills.tip.skill.p1.K_x-5",
                         "skills.tip.skill.p1.K_x-6"],
            "p1_f_tip": ["skills.tip.skill.p1.f_tip"],
            "p2_dx_d": ["skills.tip.skill.p2.dX_d-1"],
            "p2_dphi_d": ["skills.tip.skill.p2.dX_d-2"],
            "p2_ddx_d": ["skills.tip.skill.p2.ddX_d-1"],
            "p2_ddphi_d": ["skills.tip.skill.p2.ddX_d-2"],
            "p2_K_x": ["skills.tip.skill.p2.K_x-1", "skills.tip.skill.p2.K_x-2",
                       "skills.tip.skill.p2.K_x-3"],
            "p2_K_phi": ["skills.tip.skill.p2.K_x-4", "skills.tip.skill.p2.K_x-5",
                         "skills.tip.skill.p2.K_x-6"]
        }
        return context_mapping

    def get_initial_values(self):
        x_0 = dict()
        for p in self.limits:
            x_0[p] = 0.1

        return x_0

    def ground_skills(self):
        print(self.setup_instructions)
        self.learn_context["skills"]["tip"]["skill"]["objects"]["Approach"] = self.objects["Approach"]
        self.learn_context["skills"]["tip"]["skill"]["objects"]["Tippable"] = self.objects["Tippable"]
        self.setup_instructions[0]["parameters"]["skills"]["move"]["skill"]["objects"]["goal_pose"] = self.objects[
            "Approach"]
        self.reset_instructions[0]["parameters"]["skills"]["move"]["skill"]["objects"]["goal_pose"] = self.objects[
            "Approach"]

    def run_setup(self) -> bool:
        s = ServerProxy("http://collective-control-001:8000", allow_none=True)
        s.subscribe_to_event("tippable_pressed", self.robot, "12000")
        return True
