import json
import matplotlib.pyplot as plt


def cc_parser(data):
    if not isinstance(data, dict):
        print("wrong format")
        return

    cc_and_info = []
    for filename in data.keys():
        for entity in data[filename]:
            complexity = entity["complexity"]
            description = f'name: {entity["name"]}\n' \
                          f'type: {entity["type"]}\n' \
                          f'rank: {entity["rank"]}\n' \
                          f'complexity: {entity["complexity"]}\n' \
                          f'filename: {filename}'

            cc_and_info.append((complexity, description))

    cc_and_info.sort(key=lambda entry: entry[0], reverse=True)
    complexities = [complexity for complexity, _ in cc_and_info]
    cc_info = [info for _, info in cc_and_info]

    fig = plt.figure(figsize=(10, 5), frameon=True, layout="constrained")
    plt.title("Cyclomatic complexity")
    plt.xlabel("Blocks")
    plt.ylabel("Cyclomatic complexity")
    plt.grid()
    plt.xticks(visible=False)

    plt_bar = plt.bar(
        x=cc_info,
        height=complexities,
        align='edge',
        picker=True
    )

    plt_labels = []

    text_kwargs = dict(
        ha='left',
        va='top',
        color='C1',
        bbox=dict(facecolor='white', alpha=0.8),
        visible=False
    )

    for index, bar in enumerate(plt_bar.patches):
        text = plt.annotate(
            cc_info[index],
            xy=(bar.get_x(), bar.get_y() + bar.get_height()),
            xytext=(50, -50),
            textcoords='offset pixels',
            arrowprops=dict(arrowstyle='->'),
            annotation_clip=True,
            **text_kwargs
        )
        plt_labels.append(text)

    def on_pick(event):
        bar = event.artist
        print(bar)
        bar_index = plt_bar.index(bar)
        print(cc_info[bar_index])
        is_visible = plt_labels[bar_index].get_visible()
        plt_labels[bar_index].set_visible(not is_visible)
        fig.canvas.draw()

    fig.canvas.mpl_connect('pick_event', on_pick)
    plt.show()


with open("cc_results.json", "r") as f:
    cc_parser(json.loads(f.read()))
