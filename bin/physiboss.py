# PhysiBoSS Tab
import os
from ipywidgets import Layout, Label, Text, Checkbox, Button, HBox, VBox, Box, \
    FloatText, BoundedIntText, BoundedFloatText, HTMLMath, Dropdown, interactive, Output
from collections import deque, Counter
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
import matplotlib.colors as mplc
import numpy as np
import glob
import platform
import numpy as np
import csv
import itertools

# from debug import debug_view


class PhysiBoSSTab(object):

    def __init__(self):
        # tab_height = '520px'
        # tab_layout = Layout(width='900px',   # border='2px solid black',
        #                     height=tab_height, overflow_y='scroll')

        self.output_dir = '.'

        constWidth = '180px'

#        self.fig = plt.figure(figsize=(6, 6))
        # self.fig = plt.figure(figsize=(7, 7))

        max_frames = 0
        self.svg_plot = interactive(self.create_area_chart, frame=(0, max_frames), continuous_update=False)
        plot_size = '500px'  # small: controls the size of the tab height, not the plot (rf. figsize for that)
        plot_size = '700px'  # medium
        plot_size = '750px'  # medium
        self.svg_plot.layout.width = '1000px'
        self.svg_plot.layout.height = '700px'
        self.use_defaults = True
        
        self.axes_min = 0.0
        self.axes_max = 2000   # hmm, this can change (TODO?)

        self.max_frames = BoundedIntText(
            min=0, max=99999, value=max_frames,
            description='Max',
            layout=Layout(width='160px'),
#            layout=Layout(flex='1 1 auto', width='auto'),  #Layout(width='160px'),
        )
        self.max_frames.observe(self.update_max_frames)

        items_auto = [Label('select slider: drag or left/right arrows'), 
            self.max_frames, 
        ]

        box_layout = Layout(display='flex',
                    flex_flow='row',
                    align_items='stretch',
                    width='70%')
        row1 = Box(children=items_auto, layout=box_layout)

        self.tab = VBox([row1, self.svg_plot])
        self.count_dict = {}
        self.file_dict = {}

    def update(self, rdir=''):
        # with debug_view:
        #     print("SVG: update rdir=", rdir)        

        if rdir:
            self.output_dir = rdir

        all_files = sorted(glob.glob(os.path.join(self.output_dir, 'snapshot*.svg')))
        if len(all_files) > 0:
            last_file = all_files[-1]
            self.max_frames.value = int(last_file[-12:-4])  # assumes naming scheme: "snapshot%08d.svg"

        # self.create_dict(self.max_frames.value, self.output_dir)
        # self.state_counter(self.max_frames.value)
        
        # with debug_view:
        #     print("SVG: added %s files" % len(all_files))


    def update_max_frames(self,_b):
        self.svg_plot.children[0].max = self.max_frames.value

    #-------------------------
    def plot_states(self, frame):
        # global current_idx, axes_max
        global current_frame
        current_frame = frame
        fname = "snapshot%08d.svg" % frame
        full_fname = os.path.join(self.output_dir, fname)
        
        if not os.path.isfile(full_fname):
            print("Once output files are generated, click the slider.")   
            return
            
        tree = ET.parse(full_fname)
        root = tree.getroot()
        
        numChildren = 0
        for child in root:
        
            if self.use_defaults and ('width' in child.attrib.keys()):
                self.axes_max = float(child.attrib['width'])
        
            if child.text and "Current time" in child.text:
                svals = child.text.split()
                title_str = svals[2] + "d, " + svals[4] + "h, " + svals[7] + "m"

        title_str += " (" + str(num_cells) + " agents)"
        self.fig = plt.figure(figsize=(15, 15))

        plt.xlim(self.axes_min, self.axes_max)
        plt.ylim(self.axes_min, self.axes_max)

        plt.title(title_str)



    def create_dict(self, number_of_files, folder):
        "create a dictionary with the states file in the folder 'output', half of the dict is used to calculate the percentage of the node, the other half is for the states"
        # if not os.path.isfile("%sstates_00000000.csv" % folder):
        #     return
            
        self.file_dict = {}
        if number_of_files > 0:
            for i in range (0, number_of_files):
                nodes_dict = {}
                states_dict = {}
                with open('%s//states_%08u.csv' %(folder,i), newline='') as csvfile:
                    has_header = csv.Sniffer().has_header(csvfile.read(1024))
                    csvfile.seek(0)
                    states_reader = csv.reader(csvfile, delimiter=',')
                    if has_header:
                        next(states_reader)
                    for row in states_reader:
                        states_dict[row[0]] = row[1]
                        nodes_dict[row[0]] = row[1].replace("--", "").split()
                self.file_dict["node_step{0}".format(i)] = nodes_dict
                self.file_dict["state_step{0}".format(i)] = states_dict

                # print(self.file_dict)
            # return file_dict


    def state_counter(self, number_of_files):
        "create a dict with the states of the network, it can be used to print states pie chart"
        self.count_dict = {}
        if number_of_files > 0:
            for i in range (0, number_of_files):
                state_list = []
                for key in self.file_dict["state_step{0}".format(i)]:
                    for value in self.file_dict["state_step{0}".format(i)][key]:
                        state_list.append(self.file_dict["state_step{0}".format(i)][key])
                state_counts = Counter(state_list)
                fix_count_dict = {}
                for key, group in itertools.groupby(state_counts, lambda k: 'others' if (state_counts[k]<(1* (len(self.file_dict)))) else k):
                    fix_count_dict[key] = sum([state_counts[k] for k in list(group)])
                self.count_dict["state_count{0}".format(i)] = fix_count_dict
            
            # return self.count_dict

    def create_area_chart(self, frame=None):
        "plot an area chart with the evolution of the network states during the simulation"

        self.create_dict(frame, self.output_dir)
        self.state_counter(frame)
        
        state_list = []
        all_state = []
        a = []
        for k in self.count_dict:
            state_list.append(list(self.count_dict[k].keys()))
            for l in state_list:
                for state in l:
                    all_state.append(state)
        all_state = list(dict.fromkeys(all_state))
        
        for state_count in self.count_dict:
            b = []
            for states in all_state:
                try:
                    b.append(self.count_dict[state_count][states])
                except:
                    b.append(0)
            a.append(b)
        a = np.array(a)
        #print(a)
        a = np.transpose(a)
        percent = a /  a.sum(axis=0).astype(float) * 100
        x = np.arange(len(self.count_dict))
        self.fig = plt.figure(figsize=(10,7), dpi=200)
        ax = self.fig.add_subplot(111)
        ax.stackplot(x, percent, labels=all_state)
        ax.legend(labels=all_state, loc='upper center', bbox_to_anchor=(0.5, -0.05),shadow=True, ncol=2)
        # ax.legend(labels=all_state, bbox_to_anchor=(1.05, 1), loc='lower center', borderaxespad=0.)
        ax.set_title('100 % stacked area chart')
        ax.set_ylabel('Percent (%)')
        ax.margins(0, 0) # Set margins to avoid "whitespace"

        # plt.show()


