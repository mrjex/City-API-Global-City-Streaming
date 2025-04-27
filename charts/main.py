import sys

#sys.path.append('..')
#import charts.bubbleChart as bubbleChart

# import bubbleChart    # TEMPORARY COMMENTED OUT
# import pieChart       # TEMPORARY COMMENTED OUT
import equatorChart


# ARGUMENTS:
#   Argument 1: visualizeBubbleChart        = ['True' or 'False']
#   Argument 2: visualizePieChart           = ['True' or 'False']
#   Argument 3: visualizeEquatorChart       = ['True' or 'False']


numExpectedArguments = 4
numInputArguments = len(sys.argv)


def visualizeBubbleCharts():
    # bubbleChart.plotBubbleChart()
    print("TEMPORARY COMMENTED OUT")

def visualizePieCharts():
    # pieChart.plotPieChart()
    print("TEMPORARY COMMENTED OUT")

def visualizeEquatorChart():
    return equatorChart.plotEquatorChart()


def main():
    figure_json = None

    # If the developer by mistake inputs the wrong number of arguments,
    # then default to plotting all charts and printing a warning
    if numInputArguments != numExpectedArguments:
        print("Warning: No more or less than 3-boolean arguments are expected to run '/charts/main.py'")

        visualizeBubbleCharts()
        visualizePieCharts()
        figure_json = visualizeEquatorChart()
    else:
        # Check each argument and execute corresponding function
        if sys.argv[1] == 'True':
            visualizeBubbleCharts()
        
        if sys.argv[2] == 'True':
            visualizePieCharts()
        
        if sys.argv[3] == 'True':
            figure_json = visualizeEquatorChart()

    return figure_json

if __name__ == "__main__":
    figure_json = main()
    if figure_json:
        print("FIGURE_JSON_START")
        print(figure_json)
        print("FIGURE_JSON_END")