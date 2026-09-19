from fpdf import FPDF
from io import BytesIO
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
import numpy as np
import datetime as dt
from bokeh.plotting import figure
# from bokeh.models import Range1d, Panel, Tabs
from bokeh.palettes import Category20_20 as palette
from app.env import *
import logging
logging.getLogger('matplotlib').setLevel(logging.WARNING)

A4 = (210, 297)
FRAME_BORDER = 0

def get_table_height(df, cell_h):

    # Compute correct table height
    if isinstance(df.columns, pd.MultiIndex):
        nb_df_rows = len(df.columns[0])
    else:
        nb_df_rows = 1

    # Add the number of data rows
    nb_df_rows += len(df)

    table_h = cell_h * nb_df_rows

    return table_h

def renderLatex(formula, fontsize=12, dpi=300, format='svg', file=None):
    """Renders LaTeX formula into image or prints to file.
    """
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, u'${}$'.format(formula), fontsize=fontsize)

    output = BytesIO() if file is None else file
    # with warnings.catch_warnings():
    #     warnings.filterwarnings('ignore', category=MathTextWarning)
    fig.savefig(output, dpi=dpi, transparent=True, format=format,
                bbox_inches='tight', pad_inches=0.0)

    plt.close(fig)

    if file is None:
        output.seek(0)
        return output

class DatasheetReport(FPDF):

    def __init__(self, ds_data):
        # PDF setup
        super().__init__()

        self.width, self.height = A4

        self.size_margin = 5  # setting as var because it's used throughout the doc
        self.set_margin(self.size_margin)

        # Add unicode-compatible fonts
        dejavu_path = Path(RESOURCES_PATH, 'DejaVuSans.ttf')
        dejavu_b_path = Path(RESOURCES_PATH, 'DejaVuSans-Bold.ttf')
        self.add_font('DejaVu', '', dejavu_path, uni=True)
        self.add_font('DejaVu', 'B', dejavu_b_path, uni=True)

        ############
        #  Colors  #
        ############

        # Color of the text in the header
        self.header_text_color = [255, 255, 255]
        # Color of the header background
        self.header_fill_color = [0, 112, 192]
        # Color of the disclaimer text
        self.nb_text_color = [0, 88, 125]

        # Datasheet template data
        self.ds_data = ds_data

    def _print_header_data_pairs(self, x, y, key_width, value_width, cell_height, key_txt, value_txt):

        # Set the cursor at the begining of the first cell
        self.set_xy(x, y)

        self.set_font('DejaVu', '')

        # Key cell
        self.cell(
            w=key_width,
            h=cell_height,
            txt=key_txt,
            border=0,  # don't show border
            ln=0,  # move the cursor to the right
            align='R',
            fill=False

        )

        self.set_font('DejaVu', 'b')

        # Value cell
        self.cell(
            w=value_width,
            h=cell_height,
            txt=value_txt,
            border=0,
            ln=0,  # move the cursor to the right
            align='C',
            fill=False

        )

        return

    def _print_header_data(self, init_x, init_y, key_width, value_width, total_height, data_tuples):

        y_increment = total_height / len(data_tuples)

        for idx, (key_txt, value_txt) in enumerate(data_tuples):

            self._print_header_data_pairs(
                x=init_x,
                y=init_y + idx * y_increment,
                key_width=key_width,
                value_width=value_width,
                cell_height=y_increment,
                key_txt=key_txt,
                value_txt=value_txt
            )

    def header(self):

        # Colored header cells with the title and subtitle

        title_height = 7
        subtitle_height_1 = 5
        subtitle_height_2 = 5
        if self.ds_data['gauge'] == int(self.ds_data['gauge']):
            gauge = f"{self.ds_data['gauge']:.1f} mm"  
        else:
            gauge = f"{self.ds_data['gauge']} mm"   
        comm_name_w_gauge = f"{self.ds_data['commercial_name']} {gauge}"
        # Header size
        # width == 0 -> header extends over the whole width of the page
        self.header_frame_size = (0, title_height + subtitle_height_1 + subtitle_height_2)

        title = "Simulation Data Novelis"
        sub_title_2 = "Material Source: "
        sub_title_2 += self.ds_data['m_source']
        self.set_font('DejaVu', 'B', 13)
        self.set_text_color(*self.header_text_color)
        self.set_fill_color(*self.header_fill_color)
        self.cell(self.header_frame_size[0], title_height, title, 0, 1, 'C', fill=True)
        self.set_font_size(10)
        self.cell(self.header_frame_size[0], subtitle_height_1, comm_name_w_gauge, 0, 1, 'C', fill=True)
        self.cell(self.header_frame_size[0], subtitle_height_2, sub_title_2, 0, 1, 'C', fill=True)

        # Logo
        image_edge_height = 20.6  # Set the desired height for the logo
        image_edge_width = 20.6 # Set the desired width for the logo, can adjust proportionally
        # Set the logo's position, maintaining the current origin position
        self.set_xy(self.size_margin, self.size_margin - 0.085 * image_edge_height)  # Adjust to origin position
        logo_path = Path(RESOURCES_PATH, 'novelis_logo_thumbnail.jpg')
        self.image(logo_path, w=image_edge_width, h=image_edge_height)

        # Header number/availability info
        str_datasheet = str(self.ds_data['datasheet'])
        str_issue_date = str(self.ds_data['latest_revalidation'])
        str_next_check = str(self.ds_data['valid_until'])
        header_data = (
            ("N° Datasheet", str_datasheet),
            ("Issue Date", str_issue_date),
            ("Validity Date", str_next_check),
        )

        self.set_font('DejaVu', '', 7)
        self._print_header_data(
            init_x=162,
            init_y=self.size_margin,
            key_width=25,
            value_width=0,  # Value cell extends to the end of the page
            total_height=self.header_frame_size[1],  # Total height of header
            data_tuples=header_data
        )

        pass

    def footer(self):

        return

        footer_height = 5

        init_x = self.size_margin
        init_y = -self.size_margin - footer_height

        self.set_xy(init_x, init_y)

        self.cell(
            w=0,
            h=footer_height,
            txt="FOOTER",
            border=FRAME_BORDER,
            align='C',
        )

        self.set_font('DejaVu', '', 7)

        key_width = 20
        value_width = 45

        x = A4[0] - key_width - value_width - self.size_margin
        y = init_y + footer_height/2

        self._print_header_data_pairs(
            x=x,
            y=y,
            key_width=key_width,
            value_width=value_width,
            cell_height=footer_height/3,
            key_txt="Generated on:",
            value_txt=dt.datetime.now(timezone.utc).isoformat()
        )

        pass

    # Create different parts of the document
    def _print_frame_title(self, x, y, frame_title):

        self.set_font('DejaVu', 'bu', size=11)
        self.set_xy(x, y)
        self.cell(
            w=0,  # width
            h=9,
            txt=frame_title)

        return

    def _print_basic_table(self, x, y, cell_h, cell_w, np_array, border=None):

        border_outer = False
        border_inner = False

        if border == 'outer':
            border_outer = True
        elif border == 'inner':
            border_inner = True
        elif border == 'full':
            border_outer = True
            border_inner = True

        len_y, len_x = np_array.shape
        for idx, i_row in enumerate(np_array):

            iter_y = y + idx * cell_h
            for iidx, i_val in enumerate(i_row):

                iter_x = x + iidx * cell_w

                i_border = ""
                if border_outer:
                    # Top and bottom borders
                    if idx == 0:
                        i_border += "T"
                    if idx == (len_y - 1):
                        i_border += "B"
                    # Left and right borders
                    if iidx == 0:
                        i_border += "L"
                    if iidx == (len_x - 1):
                        i_border += "R"
                if border_inner:
                    # Vertical cell borders
                    if idx == 0:
                        i_border += "B"
                    else:
                        i_border += "T"
                    # Horizontal cell borders
                    if iidx == 0:
                        i_border += "R"
                    else:
                        i_border += "L"

                self.set_xy(iter_x, iter_y)

                self.cell(
                    w=cell_w,
                    h=cell_h,
                    txt=str(i_val),
                    border=i_border,
                    align='C'
                )

    def _print_combined_index(self, x, y, cell_h, cell_w, np_array, border=None):

        orig_x = self.x
        orig_y = self.y

        # Print every column in order

        # Assuming the values are grouped all in one group, and after it's finished
        # the value will not come up anymore.
        # This should be correct for dataframe indeces

        for idx_col in range(np_array.shape[1]):
            iter_x = x + idx_col * cell_w

            iter_col = np_array[:, idx_col]
            iter_counts = Counter(iter_col)

            iter_y = y
            for i_key, i_count in iter_counts.items():

                self.set_xy(iter_x, iter_y)

                self.cell(
                    w=cell_w,
                    h=i_count * cell_h,
                    txt=str(i_key),
                    border=""
                )

                iter_y += i_count * cell_h

        self.set_xy(orig_x, orig_y)

        raise NotImplementedError

        return

    def _print_dataframe(self, init_x, init_y, w, h, df):

        orig_x = self.x
        orig_y = self.y

        self.set_xy(init_x, init_y)
        # Test cell please ignore
        self.cell(
            w=w,
            h=h,
            border=0
        )

        # Get total number of columns
        if isinstance(df.index, pd.MultiIndex):
            # index_is_multiindex = True
            len_index_cols = len(df.index[0])
        else:
            # index_is_multiindex = False
            len_index_cols = 1
        total_cols = len_index_cols + len(df.columns)

        # Get total number of rows
        if isinstance(df.columns, pd.MultiIndex):
            len_index_names = len(df.columns[0])
            # columns_is_multiindex = True
        else:
            len_index_names = 1
            # columns_is_multiindex = False
        total_rows = len_index_names + len(df.index)

        # Compute cell base size
        cell_w = w/total_cols
        cell_h = h/total_rows

        # Print index names
        # (Assuming index names is multiindex when columns is multiindex)
        np_index_names = np.array(df.index.names).T

        # If table is unidimensional reshape to be correctly sized
        if np_index_names.ndim == 1:
            np_index_names = np_index_names.reshape((1, -1))

        self._print_basic_table(
            x=init_x,
            y=init_y,
            cell_h=cell_h,
            cell_w=cell_w,
            np_array=np_index_names,
            border='outer'
        )

        # Print index
        index_x = init_x
        index_y = init_y + len_index_names * cell_h

        np_index = np.array(df.index.to_list())

        # If table is unidimensional reshape to be correctly sized
        if np_index.ndim == 1:
            np_index = np_index.reshape((-1, 1))

        # self._print_combined_index(
        #     x = init_x,
        #     y = init_y,
        #     cell_h = cell_h,
        #     cell_w = cell_w,
        #     np_array = np_index,
        #     border = 'outer'
        # )

        self._print_basic_table(
            x=index_x,
            y=index_y,
            cell_h=cell_h,
            cell_w=cell_w,
            np_array=np_index,
            border='outer'
        )

        # Print columns

        cols_x = init_x + len_index_cols * cell_w
        cols_y = init_y

        np_cols_names = np.array(df.columns.to_list()).T

        # If table is unidimensional reshape to be correctly sized
        if np_cols_names.ndim == 1:
            np_cols_names = np_cols_names.reshape((1, -1))

        self._print_basic_table(
            x=cols_x,
            y=cols_y,
            cell_h=cell_h,
            cell_w=cell_w,
            np_array=np_cols_names,
            border='outer'
        )

        # Print data
        data_x = cols_x
        data_y = index_y

        # This array should be 2d in all cases
        np_data = df.values

        self._print_basic_table(
            x=data_x,
            y=data_y,
            cell_h=cell_h,
            cell_w=cell_w,
            np_array=np_data,
            border='outer'
        )

        self.set_xy(orig_x, orig_y)
        return

    def create_mech_properties(self):

        self.mech_properties_frame_size = (0, 60)

        disclaimer_height = 0
        bottom_space = 2

        init_x = self.size_margin
        init_y = self.size_margin + self.header_frame_size[1]

        # Complete frame border (used for debug)
        self.set_xy(init_x, init_y)
        self.cell(
            *self.mech_properties_frame_size,
            border=FRAME_BORDER,
            ln=2
        )

        # Frame title
        frame_title = "Mechanical Properties in Tensile Tests (ISO 6892-1)"
        self._print_frame_title(init_x, init_y, frame_title)

        cell_h = 4
        max_table_h = 45
        table_h = get_table_height(self.ds_data['df_tensile_results'], cell_h)

        table_h = min(table_h, max_table_h)
        table_w = 150

        # Center the table in the available space
        avail_h = self.mech_properties_frame_size[1] - (self.y - init_y) - disclaimer_height - bottom_space
        free_h = avail_h - table_h

        table_y_offset = 1

        table_x = init_x + 25
        table_y = self.y + free_h/2 + table_y_offset

        # Print df_tensile table contents
        self.set_font('DejaVu', "", size=7)
        self._print_dataframe(
            init_x=table_x,
            init_y=table_y,
            w=table_w,
            h=table_h,
            df=self.ds_data['df_tensile_results'],
        )

        pass

    def _create_hardening_plot(self):

        df_model_data = self.ds_data['df_model_data']

        f_out = BytesIO()

        plt.figure()
        ax = plt.gca()

        # Plot the curves only if df not empty (can still show empty plot if no data)
        if not df_model_data.empty:
            for idx, i_col in enumerate(df_model_data.columns):
                df_model_data.plot(kind='line', y=i_col, ax=ax, linewidth=3, color=palette[idx])
            plt.legend(loc='lower right')

        # Correctly set up the axes
        ax.set_xlabel("True Plastic Strain [-]")
        ax.set_ylabel("True Stress [MPa]")

        plt.savefig(f_out, dpi=300, bbox_inches='tight')
        self.hardening_plot_image = f_out

        return

    def _create_flc_plot(self):

        df_flc_raw = self.ds_data['df_flc_raw']
        df_flc_fit = self.ds_data['df_flc_fit']

        f_out = BytesIO()

        plt.figure()
        ax = plt.gca()

        if not df_flc_raw.empty:
            # Plot measurement points
            x_data = df_flc_raw['s_minor']
            y_data = df_flc_raw['s_major']

            plt.scatter(x_data, y_data, s=25, color='black', label='Mean test sample')

        # Plot Volvo fit

        if not df_flc_fit.empty:
            x_data = df_flc_fit.loc[:, 's_minor']
            y_data = df_flc_fit.loc[:, 's_major']
            sig_minus_data = df_flc_fit.loc[:, 's_major_minus_sigma']
            sig_plus_data = df_flc_fit.loc[:, 's_major_plus_sigma']
            plt.plot(x_data, y_data, linewidth=3, label='FLC')
            plt.fill_between(x_data, sig_minus_data, sig_plus_data, alpha=0.2, label=r'±1 $\sigma$ ')
        else:
            plt.savefig(f_out, dpi=300, bbox_inches='tight')
            self.flc_plot_image = f_out
            return

        # Plot dotted lines
        plt.plot([-0.5, 0], [1, 0], color='black', linestyle='--')
        plt.plot([0, 1], [0, 1], color='black', linestyle='--')

        # Adjust the axes size
        # plt.xlim([25, 50])
        x_data_min = x_data.min()

        if x_data_min > 0:
            x_min = 0.8 * x_data_min
        else:
            x_min = 1.2 * x_data_min

        x_max = 1.2 * x_data.max()
        plt.xlim([x_min, x_max])

        y_data_min = y_data.min()
        y_data_max = y_data.max()

        y_min = 0.8 * y_data_min
        y_min = min(y_min, 0)
        y_max = 1.2 * y_data_max

        plt.ylim([y_min, y_max])

        # Correctly set up the axes
        ax.set_xlabel("Minor Strain [-]")
        ax.set_ylabel("Major Strain [-]")

        plt.legend(loc='lower right')
        plt.savefig(f_out, dpi=300, bbox_inches='tight')

        self.flc_plot_image = f_out

    def create_hardening_aging(self):

        frame_width = (A4[0] - 2 * self.size_margin) / 2
        self.hardening_aging_frame_size = (frame_width, 70)

        frame_border = 5

        init_x = self.size_margin
        init_y = \
            self.size_margin +\
            self.header_frame_size[1] +\
            self.mech_properties_frame_size[1]

        # Complete frame border (used for debug)
        self.set_xy(init_x, init_y)
        self.cell(
            *self.hardening_aging_frame_size,
            border=FRAME_BORDER,
            ln=2
        )

        # Frame title
        frame_title = "Hardening"
        self._print_frame_title(init_x, init_y, frame_title)

        # Hardening plot
        # image_max_width = self.hardening_aging_frame_size[0] - 2 * frame_border
        image_max_height = self.hardening_aging_frame_size[1] - 2 * frame_border

        self._create_hardening_plot()
        self.image(self.hardening_plot_image, x=init_x + 1, y=init_y + 9, w=0, h=image_max_height)
                # Hardening fit note
        hard_note_x = init_x
        hard_note_y = init_y + 72
        self.set_xy(hard_note_x, hard_note_y)

        str_model_name = self.ds_data['model_name']

        str_model_name = str_model_name.replace("_", "-")
        str_model_name = str_model_name.title()
        self.set_font('DejaVu', "", size=9)
        self.multi_cell(
            h=5,
            w=95,
            txt=f"Hardening curves are based on a least squares fit of a {str_model_name} " +
                "approximation to tensile tests in 0° (ISO 6892-1) and hydraulic bulge tests (ISO 16808)."
        )

    def create_hardening_aging_customer(self):

        frame_width = (A4[0] - 2 * self.size_margin) / 2
        self.hardening_aging_frame_size = (frame_width, 70)

        frame_border = 5

        init_x = self.size_margin
        init_y = \
            self.size_margin +\
            self.header_frame_size[1] +\
            self.mech_properties_frame_size[1]

        # Complete frame border (used for debug)
        self.set_xy(init_x, init_y)
        self.cell(
            *self.hardening_aging_frame_size,
            border=FRAME_BORDER,
            ln=2
        )

        # Frame title
        frame_title = "Hardening"
        self._print_frame_title(init_x, init_y, frame_title)

        # Hardening plot
        # image_max_width = self.hardening_aging_frame_size[0] - 2 * frame_border
        image_max_height = self.hardening_aging_frame_size[1] - 2 * frame_border

        self._create_hardening_plot()
        # self.image(self.hardening_plot_image, x=init_x + 10, y=init_y + 9, w=0, h=image_max_height)
        # Adjust x position to move plot to the left and center above the caption
        plot_x_offset = 3  # Adjust this value to move left
        self.image(self.hardening_plot_image, x=init_x + plot_x_offset, y=init_y + 9, w=0, h=image_max_height)

                # Hardening fit note
        hard_note_x = init_x
        hard_note_y = init_y + 72
        self.set_xy(hard_note_x, hard_note_y)

        str_model_name = self.ds_data['model_name']

        str_model_name = str_model_name.replace("_", "-")
        str_model_name = str_model_name.title()
        self.set_font('DejaVu', "", size=9)
        self.multi_cell(
            h=5,
            w=95,
            txt=f"Hardening curves are based on a least squares fit of a {str_model_name} " +
                "approximation to tensile tests in 0° (ISO 6892-1) and hydraulic bulge tests (ISO 16808). " +
                "Hardening curves are available as a table in a separate ascii file."
        )

    def create_forming_diagram(self):

        self.forming_diagram_frame_size = (0, self.hardening_aging_frame_size[1])
        frame_border = 5

        init_x = self.size_margin + self.hardening_aging_frame_size[0]
        init_y = \
            self.size_margin +\
            self.header_frame_size[1] +\
            self.mech_properties_frame_size[1]

        # Complete frame border (used for debug)
        self.set_xy(init_x, init_y)
        self.cell(
            *self.forming_diagram_frame_size,
            border=FRAME_BORDER,
            ln=2
        )

        # Frame title
        frame_title = "Forming Limit Diagram "
        self._print_frame_title(init_x, init_y, frame_title)

        # Hardening plot
        image_h = self.hardening_aging_frame_size[1] - 2 * frame_border

        self._create_flc_plot()
        
        
        self.image(self.flc_plot_image, x=init_x + 3, y=init_y + 9, w=0, h=image_h)
        graph_note_x = init_x
        graph_note_y = init_y + 72
        self.set_xy(graph_note_x, graph_note_y)

        self.set_font('DejaVu', "", size=9)
        self.multi_cell(
            h=5,
            w=95,
            txt=f"Forming limit test results and forming limit curve are based on ISO 12004-2."
        )

    def create_fitting_data(self):

        self.fitting_data_frame_size = (0, 35)

        hard_note_height = 10
        bottom_space = 2

        init_x = self.size_margin
        init_y = \
            self.size_margin +\
            self.header_frame_size[1] +\
            self.mech_properties_frame_size[1] +\
            self.hardening_aging_frame_size[1]

        # Complete frame border (used for debug)
        self.set_xy(init_x, init_y)
        self.cell(
            *self.fitting_data_frame_size,
            border=FRAME_BORDER,
            ln=2
        )

        cell_h = 4
        max_table_h = 18
        table_h = get_table_height(self.ds_data['df_model_params'], cell_h)

        # Print df_model_params table contents
        table_h = min(table_h, max_table_h)
        table_w = 150

        # Center the table in the available space
        avail_h = self.fitting_data_frame_size[1] - (self.y - init_y) - hard_note_height - bottom_space
        free_h = avail_h - table_h

        table_y_offset = 3

        table_x = init_x + (A4[0] - table_w - self.size_margin) / 2
        table_y = self.y + free_h/2 + table_y_offset

        self.set_font('DejaVu', "", size=7)

        # Map internal names to symbols for display in the table
        symbol_mapping = {
            "sig_i": "σᵢ",
            "sig_sat": "σₛₐₜ",
            "a": "a",
            "p": "p",
            "C": "C",
            "eps_0": "ϵ₀",
            "m": "m",
            "alpha": "α"
        }

        # Replace column headers with symbols for display
        df_model_params_display = self.ds_data['df_model_params'].copy()
        df_model_params_display.columns = [
            symbol_mapping.get(col, col) for col in df_model_params_display.columns
        ]

        self._print_dataframe(
            init_x=table_x,
            init_y=table_y,
            w=table_w,
            h=table_h,
            df=df_model_params_display.round(6),
        )

        # Print latex model formula
        formula_x = table_x + 50
        formula_y = table_y - 5

        latex_formula = self.ds_data['model_latex']

        f_latex_formula = renderLatex(latex_formula, fontsize=8, format='png')

        self.image(f_latex_formula, formula_x, formula_y, h=4)

        # Hardening fit note
        # hard_note_x = init_x
        # hard_note_y = init_y + self.fitting_data_frame_size[1] - hard_note_height - bottom_space
        # self.set_xy(hard_note_x, hard_note_y)

        # str_model_name = self.ds_data['model_name']

        # str_model_name = str_model_name.replace("_", "-")
        # str_model_name = str_model_name.title()

        # self.set_font('DejaVu', "", size=9)
        # self.multi_cell(
        #     h=5,
        #     w=0,
        #     txt=f"Hardening curves are based on a least squares fit of a {str_model_name} " +
        #         "approximation to tensile tests in 0° (ISO 6892-1) and hydraulic bulge tests (ISO 16808)"
        # )

        return

    def create_yield_surface(self):

        self.yield_surface_frame_size = (0, 60)

        yield_warn_height = 15
        bottom_space = 2

        init_x = self.size_margin
        init_y = \
            self.size_margin +\
            self.header_frame_size[1] +\
            self.mech_properties_frame_size[1] +\
            self.hardening_aging_frame_size[1] +\
            self.fitting_data_frame_size[1]+15

        # Complete frame border (used for debug)
        self.set_xy(init_x, init_y)
        self.cell(
            *self.yield_surface_frame_size,
            border=FRAME_BORDER,
            ln=2
        )

        # Frame title
        frame_title = "Yield surface"
        self._print_frame_title(init_x, init_y, frame_title)

        # Yield model description
        self.ln(10)

        self.set_font('DejaVu', '', size=9)

        self.multi_cell(
            h=5,
            w=0,
            txt="Novelis recommends using the BBC 2005 model, the Barlat 2000 model or even more" + 
            " complex models that involves several variables to compute the yield surface. Uniform tension and"  + 
            " bulge ratios σi/σ0 and σb/σ0 are obtained from correspondng tests and (rbi =1) is an assumption."
        )

        # Print df_tensile table contents

        cell_h = 4
        max_table_h = 17
        table_h = get_table_height(self.ds_data['df_yield'], cell_h)

        # Set the table width and height
        table_h = min(table_h, max_table_h)
        table_w = 150

        # Center the table in the available space
        avail_h = self.yield_surface_frame_size[1] - (self.y - init_y) - yield_warn_height - bottom_space
        free_h = avail_h - table_h

        table_y_offset = 1
        table_x = init_x + 25
        table_y = self.y + free_h/2 + table_y_offset

        self.set_font('DejaVu', "", size=9)
        self._print_dataframe(
            init_x=table_x,
            init_y=table_y,
            w=table_w,
            h=table_h,
            df=self.ds_data['df_yield'],
        )

        # Yield warning

        # yield_warn_x = init_x
        # yield_warn_y = init_y + self.yield_surface_frame_size[1] - yield_warn_height
        # self.set_xy(yield_warn_x, yield_warn_y)

        # self.set_font('DejaVu', '', size=9)
        # self.multi_cell(
        #     h=5,
        #     w=0,
        #     txt="Warning: When using BBC 2005 (or any other yield surface), the user should enter " +
        #         "all required paramteres. Incomplete entries bear the risk of a strong deviation of the " +
        #         "yield surface from the actual material behaviour and incorrect simulation results."
        # )

        self.ln(15)
        self.add_page()
        disc_x = init_x
        disc_y = self.size_margin + self.header_frame_size[1] + 4  # Adjust the position below the header and logo
        self.set_xy(disc_x, disc_y)
        self.set_font('DejaVu', "u", size=9)
        self.cell(txt="Disclaimer:", align='L', ln=1)
        self.ln()

        disclaimer_list = [
           "Novelis Inc. (“Novelis”) wishes to provide this material Data Sheet (“Data Sheet”) to the Receiving Party (“Party”). Novelis is not responsible for (i) any processing done by the Party to any materials that are related to the Data Sheet, and (ii) the use of the Data Sheet for compliance validation by a third party.  The Data Sheet is being provided for information about typical material properties only. Therefore, Novelis makes no representations and extends no warranties of any kind, express or implied, concerning the Data Sheet, which is provided “as is.”  There are no express or implied warranties of merchantability or fitness for a particular purpose, or that the use of the Data Sheet will not infringe any patent, copyright, trademark, or other proprietary right of any third party. Novelis will not be liable to the Party whether in contract, tort, equity or otherwise, for any indirect, incidental, special, punitive, or consequential damages arising out of or related to the Data Sheet, including, without limitation, damages for loss of anticipated business profits, business interruption, and the like, even if the Party is notified of the possibility of such damages. By accepting the Data Sheet, the Party hereby accepts the terms and conditions. "
        ]

        self.set_font('DejaVu', "", size=7)
        for i_disc in disclaimer_list:
            self.multi_cell(
                h=5,
                w=0,
                txt=f"{i_disc}",
                ln=1,
            )
            self.ln(2)

        pass

    def create_yield_surface_customer(self):

        self.yield_surface_frame_size = (0, 60)

        yield_warn_height = 15
        bottom_space = 2

        init_x = self.size_margin
        init_y = \
            self.size_margin +\
            self.header_frame_size[1] +\
            self.mech_properties_frame_size[1] +\
            self.hardening_aging_frame_size[1] + 30
            # self.fitting_data_frame_size[1]+15

        # Complete frame border (used for debug)
        self.set_xy(init_x, init_y)
        self.cell(
            *self.yield_surface_frame_size,
            border=FRAME_BORDER,
            ln=2
        )

        # Frame title
        frame_title = "Yield surface"
        self._print_frame_title(init_x, init_y, frame_title)

        # Yield model description
        self.ln(10)

        self.set_font('DejaVu', '', size=9)

        self.multi_cell(
            h=5,
            w=0,
            txt="Novelis recommends using the BBC 2005 model, the Barlat 2000 model or even more" + 
            " complex models that involves several variables to compute the yield surface. Uniform tension and"  + 
            " bulge ratios σi/σ0 and σb/σ0 are obtained from correspondng tests and (rbi =1) is an assumption."
        )

        # Print df_tensile table contents

        cell_h = 4
        max_table_h = 17
        table_h = get_table_height(self.ds_data['df_yield'], cell_h)

        # Set the table width and height
        table_h = min(table_h, max_table_h)
        table_w = 150

        # Center the table in the available space
        avail_h = self.yield_surface_frame_size[1] - (self.y - init_y) - yield_warn_height - bottom_space
        free_h = avail_h - table_h

        table_y_offset = 1
        table_x = init_x + 25
        table_y = self.y + free_h/2 + table_y_offset

        self.set_font('DejaVu', "", size=7)
        self._print_dataframe(
            init_x=table_x,
            init_y=table_y,
            w=table_w,
            h=table_h,
            df=self.ds_data['df_yield'],
        )

        # Yield warning

        # yield_warn_x = init_x
        # yield_warn_y = init_y + self.yield_surface_frame_size[1] - yield_warn_height
        # self.set_xy(yield_warn_x, yield_warn_y)

        # self.set_font('DejaVu', '', size=9)
        # self.multi_cell(
        #     h=5,
        #     w=0,
        #     txt="Warning: When using BBC 2005 (or any other yield surface), the user should enter " +
        #         "all required paramteres. Incomplete entries bear the risk of a strong deviation of the " +
        #         "yield surface from the actual material behaviour and incorrect simulation results."
        # )

        # Print disclaimer
        disc_x = init_x
        disc_y = init_y + self.yield_surface_frame_size[1] - yield_warn_height + 10

        # bullet_char = "•"
        # bullet_char = "- "
        self.set_xy(disc_x, disc_y)
        self.set_font('DejaVu', "u", size=9)
        self.cell(txt="Disclaimer:", align='L', ln=1)
        self.ln()

        disclaimer_list = [
            "Novelis Inc. (“Novelis”) wishes to provide this material Data Sheet (“Data Sheet”) to the Receiving Party (“Party”). Novelis is not responsible for (i) any processing done by the Party to any materials that are related to the Data Sheet, and (ii) the use of the Data Sheet for compliance validation by a third party.  The Data Sheet is being provided for information about typical material properties only. Therefore, Novelis makes no representations and extends no warranties of any kind, express or implied, concerning the Data Sheet, which is provided “as is.”  There are no express or implied warranties of merchantability or fitness for a particular purpose, or that the use of the Data Sheet will not infringe any patent, copyright, trademark, or other proprietary right of any third party. Novelis will not be liable to the Party whether in contract, tort, equity or otherwise, for any indirect, incidental, special, punitive, or consequential damages arising out of or related to the Data Sheet, including, without limitation, damages for loss of anticipated business profits, business interruption, and the like, even if the Party is notified of the possibility of such damages. By accepting the Data Sheet, the Party hereby accepts the terms and conditions. "
        ]

        self.set_font('DejaVu', "", size=7)
        for i_disc in disclaimer_list:
            self.multi_cell(
                h=5,
                w=0,
                txt=f"{i_disc}",
                ln=1,
            )
            self.ln(2)

        pass

    def setup(self):
        # Set the matplotlib plot parameters
        plt.rcParams.update({'font.size': 13})

    def create(self):

        # Setup parameters
        self.setup()

        # Create the page
        self.add_page()
        # Add the sections
        self.create_mech_properties()
        self.create_hardening_aging()
        self.create_forming_diagram()
        self.create_fitting_data()
        self.create_yield_surface()

    def create_customer_pdf(self):

        # Setup parameters
        self.setup()

        # Create the page
        self.add_page()
        # Add the sections
        self.create_mech_properties()
        self.create_hardening_aging_customer()
        self.create_forming_diagram()
        # self.create_fitting_data()
        self.create_yield_surface_customer()

