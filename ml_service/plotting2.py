import numpy
import numpy as np
from plotting.data_acquisition import *
from plotting.data_processor import DataProcessor
from plotting.data_processor import DataError
import matplotlib.pyplot as plt


skills_time = [
    {
        "skill_class": "insert_object",
        "task": "Insert C10",
        "host": "localhost",
        "database": "transfer_base_v2",
        "tags": ["insertion", "cylinder_10"],
        "max_cost": 10,
        "cost_thr": 10
     },
    {
        "skill_class": "insert_object",
        "task": "Insert C20",
        "host": "localhost",
        "database": "transfer_base_v2",
        "tags": ["insertion", "cylinder_20"],
        "max_cost": 10,
        "cost_thr": 10
    },
    {
        "skill_class": "insert_object",
        "task": "Insert C30",
        "host": "localhost",
        "database": "transfer_base_v2",
        "tags": ["insertion", "cylinder_30"],
        "max_cost": 10,
        "cost_thr": 10
    },
    {
        "skill_class": "insert_object",
        "task": "Insert C40",
        "host": "localhost",
        "database": "transfer_base_v2",
        "tags": ["insertion", "cylinder_40"],
        "max_cost": 10,
        "cost_thr": 10
    },
    {
        "skill_class": "insert_object",
        "task": "Insert C50",
        "host": "localhost",
        "database": "transfer_base_v2",
        "tags": ["insertion", "cylinder_50"],
        "max_cost": 10,
        "cost_thr": 10
    },
    {
        "skill_class": "insert_object",
        "task": "Insert C60",
        "host": "localhost",
        "database": "transfer_base_v2",
        "tags": ["insertion", "cylinder_60"],
        "max_cost": 10,
        "cost_thr": 10
    },
    {
        "skill_class": "insert_object",
        "task": "Insert Key",
        "host": "localhost",
        "database": "transfer_base_v2",
        "tags": ["insertion", "key_old"],
        "max_cost": 10,
        "cost_thr": 10
    },
    {
        "skill_class": "insert_object",
        "task": "Insert Pad Key",
        "host": "localhost",
        "database": "transfer_base_v2",
        "tags": ["insertion", "key_pad"],
        "max_cost": 10,
        "cost_thr": 10
    },
    {
        "skill_class": "insert_object",
        "task": "Insert Hatch Key",
        "host": "localhost",
        "database": "transfer_base_v2",
        "tags": ["insertion", "key_hatch"],
        "max_cost": 10,
        "cost_thr": 10
    },
    {
        "skill_class": "extraction",
        "task": "Extract Key",
        "host": "localhost",
        "database": "iros2021",
        "tags": ["iros2021", "extraction"],
        "max_cost": 10,
        "cost_thr": 5
    },
    {
        "skill_class": "grab",
        "task": "Grab Key",
        "host": "localhost",
        "database": "iros2021",
        "tags": ["iros2021", "grab"],
        "max_cost": 10,
        "cost_thr": 5
    },
    {
        "skill_class": "place",
        "task": "Place Key",
        "host": "localhost",
        "database": "iros2021",
        "tags": ["iros2021", "place"],
        "max_cost": 10,
        "cost_thr": 5
    },
    {
        "skill_class": "turn",
        "task": "Turn Key",
        "host": "localhost",
        "database": "iros2021",
        "tags": ["iros2021", "turn"],
        "max_cost": 10,
        "cost_thr": 5
    },
    {
        "skill_class": "move",
        "task": "Move",
        "host": "localhost",
        "database": "iros2021",
        "tags": ["iros2021", "move"],
        "max_cost": 10,
        "cost_thr": 5
    },
    # {
    #     "skill_class": "press_button",
    #     "task": "Press Button",
    #     "host": "localhost",
    #     "database": "iros2021",
    #     "tags": ["iros2021", "press_button"],
    #     "max_cost": 10,
    #     "cost_thr": 5
    # },
    {
        "skill_class": "tip",
        "task": "Tip Enter Key",
        "host": "localhost",
        "database": "diss_additional",
        "tags": ["diss_additional"],
        "max_cost": 10,
        "cost_thr": 5
    },
    {
        "skill_class": "turn_lever",
        "task": "Turn Lever",
        "host": "localhost",
        "database": "diss_additional",
        "tags": ["diss_additionals"],
        "max_cost": 10,
        "cost_thr": 5
    },
    {
        "skill_class": "drag",
        "task": "Drag Box",
        "host": "localhost",
        "database": "diss_additional",
        "tags": ["diss_additional"],
        "max_cost": 10,
        "cost_thr": 5
    },
    {
        "skill_class": "bend",
        "task": "Bend Cables",
        "host": "localhost",
        "database": "diss_additional2",
        "tags": ["diss_additional"],
        "max_cost": 10,
        "cost_thr": 5
    }
]

skills_forces = [
    {
        "skill_class": "insertion",
        "task": "cylinder_30",
        "host": "localhost",
        "database": "diss_additional2",
        "tags": ["diss_additional", "cylinder_30", "contact_forces"],
        "max_cost": 157,
        "cost_thr": 60
     },
    {
        "skill_class": "insertion",
        "task": "cylinder_40",
        "host": "localhost",
        "database": "diss_additional2",
        "tags": ["diss_additional", "cylinder_40", "contact_forces"],
        "max_cost": 100,
        "cost_thr": 60
    },
    # {
    #     "skill_class": "insertion",
    #     "task": "key_abus_e30",
    #     "host": "localhost",
    #     "database": "diss_additional2",
    #     "tags": ["diss_additional", "key_abus_e30", "contact_forces"],
    #     "max_cost": 157,
    #     "cost_thr": 60
    # },
    {
        "skill_class": "insertion",
        "task": "key_old",
        "host": "localhost",
        "database": "diss_additional2",
        "tags": ["diss_additional", "key_old", "contact_forces"],
        "max_cost": 157,
        "cost_thr": 60
    },
    {
        "skill_class": "extraction",
        "task": "cylinder_30",
        "host": "localhost",
        "database": "diss_additional2",
        "tags": ["diss_additional", "contact_forces"],
        "max_cost": 157,
        "cost_thr": 60
    },
    {
        "skill_class": "turn_lever",
        "task": "red_lever",
        "host": "localhost",
        "database": "diss_additional2",
        "tags": ["diss_additionals", "contact_forces"],
        "max_cost": 157,
        "cost_thr": 60
    },
    {
        "skill_class": "tip",
        "task": "enter_key",
        "host": "localhost",
        "database": "diss_additional2",
        "tags": ["diss_additional", "contact_forces"],
        "max_cost": 157,
        "cost_thr": 60
    },
    {
        "skill_class": "drag",
        "task": "blue_box",
        "host": "localhost",
        "database": "diss_additional2",
        "tags": ["diss_additional", "contact_forces"],
        "max_cost": 157,
        "cost_thr": 60
    },
    {
        "skill_class": "press_button",
        "task": "Press Button",
        "host": "localhost",
        "database": "diss_additional2",
        "tags": ["diss_additional", "contact_forces"],
        "max_cost": 157,
        "cost_thr": 60
    },
    {
        "skill_class": "bend",
        "task": "Bend",
        "host": "localhost",
        "database": "diss_additional2",
        "tags": ["diss_additional", "contact_forces"],
        "max_cost": 157,
        "cost_thr": 60
    },
]


def plot_experiments(config: list, cost_function: str, max_cost: int, max_time: int):
    p = DataProcessor()

    n_cols = 3
    n_rows = int(np.ceil(len(config) / n_cols))

    fig_cost, axes_cost = plt.subplots(n_rows, n_cols, sharex=True, sharey=True, gridspec_kw={'hspace': 0, 'wspace': 0})
    fig_casr, axes_casr = plt.subplots(n_rows, n_cols, sharex=True, sharey=True, gridspec_kw={'hspace': 0, 'wspace': 0})
    fig_cost.set_size_inches(6, 9)
    fig_casr.set_size_inches(6, 9)

    i = 0
    j = 0
    for c in config:
        # Axes configuration
        axes_cost[i, j].set_xlim(0, 1500)
        axes_casr[i, j].set_xlim(0, 1500)
        axes_cost[i, j].set_ylim(0, c["max_cost"])
        axes_casr[i, j].set_ylim(0, 1500)
        axes_cost[i, j].grid()
        axes_casr[i, j].grid()
        axes_cost[i, j].tick_params(axis="both", which="both", length=0)
        axes_casr[i, j].tick_params(axis="both", which="both", length=0)
        axes_cost[i, j].set_title(c["task"], y=1.0, pad=-10, x=0.2, ha="left", fontsize=10)
        axes_casr[i, j].set_title(c["task"], y=1.0, pad=-10, x=0.05, ha="left", fontsize=10)

        try:
            results = get_multiple_experiment_data(c["host"], c["skill_class"], results_db=c["database"],
                                                   filter={"meta.tags": {"$all": c["tags"]}})
        except (DataNotFoundError, DataError):
            print("Data for skill class " + c["skill_class"] + " and tags " + str(c["tags"]) + " does not exist on " +
                  c["host"] + " in database " + c["database"])
            return False
        cost, confidence_cost = p.get_average_cost_over_time(results, 1500, True)
        cost = cost[0:1500] * c["cost_thr"]
        confidence_cost = confidence_cost[0:1500] * c["cost_thr"]
        casr, confidence_casr = p.get_average_success_over_time(results)
        casr = casr[0:1500]
        confidence_casr = confidence_casr[0:1500]

        for k in range(1, len(casr)):
            casr[k] += casr[k - 1]

        axes_cost[i, j].plot(cost, linestyle="dashed", zorder=2, linewidth=4)
        axes_cost[i, j].fill_between(np.linspace(0, len(cost), len(cost)), cost - confidence_cost,
                                     cost + confidence_cost, alpha=0.2, color="blue")
        axes_casr[i, j].plot([0, len(casr)], [0, len(casr)], color="black", linestyle="dashed")
        axes_casr[i, j].plot(casr, linestyle="dashed", zorder=2, linewidth=4)
        axes_cost[i, j].fill_between(np.linspace(0, len(casr), len(casr)), casr - confidence_casr,
                                     casr + confidence_casr, alpha=0.2)
        legend_cost = [c["task"]]
        legend_casr = ["Optimal CALSC", c["task"]]

        # axes_cost[i, j].legend(legend_cost, fontsize='x-small', loc=1)
        # axes_casr[i, j].legend(legend_casr, fontsize='x-small', loc='upper left')
        # if i == 0:
        #     pass
        #     axes[i, j].annotate("t" + str(j), xy=(0.5, 1), xytext=(0, 5),
        #                         xycoords='axes fraction', textcoords='offset points',
        #                         size='large', ha='center', va='baseline')
        if j == 0:
            ticks = numpy.linspace(0, 120, 5)
            axes_cost[i, j].set_yticks(ticks)
            axes_cost[i, j].set_yticklabels(list(map(str,ticks)))
            ticks = numpy.linspace(0, max_time * 2 / 3, 3)
            ticks = [int(t) for t in ticks]
            axes_casr[i, j].set_yticks(ticks)
            axes_casr[i, j].set_yticklabels(list(map(str, ticks)))
        #     pass
        #     axes[i, j].annotate("t" + str(i), xy=(0, 0.5), xytext=(-axes[i, j].yaxis.labelpad - 5, 0),
        #                         xycoords=axes[i, j].yaxis.label, textcoords='offset points',
        #                         size='large', ha='right', va='center')
        #     axes[i, j].set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1])
        #     axes[i, j].set_yticklabels([''] * 6)
        if i == n_rows - 1:
            ticks = numpy.linspace(0, max_time*2/3, 3)
            ticks = [int(t) for t in ticks]
            axes_cost[i, j].set_xticks(ticks)
            axes_cost[i, j].set_xticklabels(list(map(str, ticks)))
            axes_casr[i, j].set_xticks(ticks)
            axes_casr[i, j].set_xticklabels(list(map(str, ticks)))

        axes_cost[i, j].tick_params(axis='both', which='major', labelsize=10)
        axes_casr[i, j].tick_params(axis='both', which='major', labelsize=10)

        j += 1
        if j == n_cols:
            i += 1
            j = 0

    ax_cost = fig_cost.add_subplot(111, frame_on=False)
    ax_casr = fig_casr.add_subplot(111, frame_on=False)
    ax_cost.tick_params(labelcolor="none", bottom=False, left=False)
    ax_casr.tick_params(labelcolor="none", bottom=False, left=False)
    ax_cost.set_xlabel("Learning Time [s]", fontsize=12)
    ax_casr.set_xlabel("Learning Time [s]", fontsize=12)
    ax_cost.set_ylabel(cost_function, fontsize=12)
    ax_casr.set_ylabel("CALSC []", fontsize=12)
    ax_casr.yaxis.set_label_coords(-0.1, 0.5)
    ax_cost.yaxis.set_label_coords(-0.1, 0.5)

    fig_cost.set_size_inches(6, 3/2*n_rows)
    fig_casr.set_size_inches(6, 3/2*n_rows)
    fig_cost.savefig("learning_exp_2_1_results_a.png", bbox_inches='tight', dpi=300)
    fig_casr.savefig("learning_exp_2_1_results_b.png", bbox_inches='tight', dpi=300)

    plt.show()


def plot_experiment(host: str, skill_class: str, database: str, tags: list, max_cost: int):
    p = DataProcessor()
    max_time = 1500
    fig, axes = plt.subplots(2, 1, sharex=True, sharey=False, gridspec_kw={'hspace': 0, 'wspace': 0})

    axes[0].set_xlim(0, 1500)
    axes[1].set_xlim(0, 1500)
    axes[0].set_ylim(0, max_cost)
    axes[1].set_ylim(0, 1500)
    axes[0].grid()
    axes[1].grid()
    axes[0].tick_params(axis="both", which="both", length=0)
    axes[1].tick_params(axis="both", which="both", length=0)
    axes[0].set_title(skill_class, y=1.0, pad=-14)
    axes[1].set_title(skill_class, y=1.0, pad=-14)

    try:
        results = get_multiple_experiment_data(host, skill_class, results_db=database,
                                               filter={"meta.tags": {"$all": tags}})
    except (DataNotFoundError, DataError):
        print("Data for skill class " + skill_class + " and tags " + str(tags) + " does not exist on " +
              host + " in database " + database)
        return False
    cost2, _ = p.get_average_cost(results, True)
    print(cost2)
    print(np.where(cost2 == 0))
    cost, confidence_cost = p.get_average_cost_over_time(results, 1500, True)
    cost = cost[0:1500] * max_cost / 2
    confidence_cost = confidence_cost[0:1500] * max_cost / 2
    casr, confidence_casr = p.get_average_success_over_time(results)
    casr = casr[0:1500]
    confidence_casr = confidence_casr[0:1500]

    for k in range(1, len(casr)):
        casr[k] += casr[k - 1]

    axes[0].plot(cost, linestyle="dashed", zorder=2, linewidth=4)
    axes[0].fill_between(np.linspace(0, len(cost), len(cost)), cost - confidence_cost,
                                 cost + confidence_cost, alpha=0.2, color="blue")
    axes[1].plot([0, len(casr)], [0, len(casr)], color="black", linestyle="dashed")
    axes[1].plot(casr, linestyle="dashed", zorder=2, linewidth=4)
    axes[1].fill_between(np.linspace(0, len(casr), len(casr)), casr - confidence_casr,
                                 casr + confidence_casr, alpha=0.2)
    legend_cost = [skill_class]
    legend_casr = ["Optimal CASR", skill_class]

    axes[0].legend(legend_cost, fontsize='x-small', loc=1)
    axes[1].legend(legend_casr, fontsize='x-small', loc='upper left')

    ticks = numpy.linspace(2, max_cost, 5)
    axes[0].set_yticks(ticks)
    axes[0].set_yticklabels(list(map(str, ticks)))
    ticks = numpy.linspace(250, max_time, 6)
    axes[1].set_xticks(ticks)
    axes[1].set_xticklabels(list(map(str, ticks)))
    axes[1].tick_params(axis='both', which='major', labelsize=12)

    plt.show()
