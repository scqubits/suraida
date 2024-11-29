#
#    This file is part of suraida.
#
#    Copyright (c) 2024 and later, Jens Koch
#    All rights reserved.
#
#    This source code is licensed under the BSD-style license found in the
#    LICENSE file in the root directory of this source tree.
############################################################################


import inspect
import warnings

from typing import Any, Callable, List, Optional, Tuple, Union

import ipyvuetify as v
import ipywidgets
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from IPython.display import display
from IPython import get_ipython

from suraida.widgets import (
    flex_column,
    flex_row,
    numeric,
    FloatEntry,
    BaseEntry,
    DiscreteSetSlider,
)


ParameterDefinition = Union[
    Tuple[str, Union[List[numeric], np.ndarray]],
    Tuple[str, Union[int, float], Union[int, float], Union[int, float]],
    Tuple[
        str,
        Union[int, float],
        Union[int, float],
        Union[int, float],
        Union[int, float],
    ],
]
VariableDefinition = Union[
    Tuple[str, Union[List[numeric], np.ndarray]],
    Tuple[str, Union[int, float], Union[int, float], Union[int, float]],
]


def default_template(
    sliders: List[v.VuetifyWidget], plot: ipywidgets.Output, controls: v.Container
) -> v.Container:
    """
    This is the default template governing the arrangement of the widgets. This layout
    places the plot output on the left, and stacks sliders in a second column to the
    right.

    Parameters
    ----------
    sliders:
        The list of sliders.
    plot:
        The plot output widget.
    controls:
        Container with save buttons.

    Returns
    -------
        An ipyvuetify.Container object which arranges the plot output and slider widgets
        in the desired fashion.

    """
    return v.Container(
        class_="d-flex flex-column",
        children=[
            v.Container(
                class_="d-flex flex-row",
                children=[
                    flex_column([plot], class_="p-0 m-0"),
                    flex_column(sliders + [controls]),
                ],
            ),
        ],
    )


class InteractivePlot:
    """
    This class facilitates interactive plotting, based on a user-provided function that
    generates the plot and names independent parameters which can be modified by sliders

    Parameters
    ----------
    plot_func:
        user-provided function expected to have the signature `plot_func(
        the signature `plot_func(ax, x1, x2, ...)`.
        Here, `x1`, `x2`, ... are parameters (those turned into sliders).
        The plot should be implemented by accessing the matplotlib Axes expected
        as the first argument,  for example via `ax.plot(...)`.
        The return value of plot_func is not used.
    param_defs:
        Specifies the name of the parameter and its allowed values
        according to three alternative formats.
        (i)   (<parameter_name>, <list-like object of allowed values>)
        (ii)  (<parameter_name>, min, max, step)
        (iii) (<parameter_name>, min, max, step, ini)
    update_plot_func:
        This is an optional parameter, providing an alternative plotting function
        for updates after the first initial plot. (If omitted, `plot_func` will
        be used for updates.)
    template:
        This optional parameter allows user-defined layouts of the user-interface,
        specifically how plot output and sliders are arranged and formatted. The
        default formatting (implemented when this argument is omitted) is governed
        by
        ``def default_template(sliders, plot):
             return v.Html(tag="div",
                           class_="d-flex flex-row align-start",
                           children=[plot, flex_column(sliders)])``

    """

    def __init__(
        self,
        plot_func: Union[Callable[[Axes, numeric, ...], Any], np.ndarray, list],
        param_defs: List[ParameterDefinition],
        update_plot_func: Optional[
            Union[Callable[[Axes, numeric, ...], Any], np.ndarray, list]
        ] = None,
        template: Optional[
            Callable[[List[v.VuetifyWidget], ipywidgets.Output], v.Container]
        ] = None,
    ):
        if isinstance(plot_func, list):
            self.plot_func_array = np.array(plot_func)
        elif callable(plot_func):
            self.plot_func_array = np.array([[plot_func]])
        else:
            self.plot_func_array = plot_func
        if self.plot_func_array.ndim == 1:
            self.plot_func_array = self.plot_func_array[
                ..., None
            ]  # turn into proper column vector

        if update_plot_func:
            if isinstance(update_plot_func, list):
                self.update_func_array = np.array(update_plot_func)
            elif callable(update_plot_func):
                self.update_func_array = np.array([[update_plot_func]])
            else:
                self.update_func_array = update_plot_func
            if self.update_func_array.ndim == 1:
                self.update_func_array = self.update_func_array[
                    ..., None
                ]  # turn into proper column vector
        else:
            self.update_func_array = self.plot_func_array

        self.nrows = self.plot_func_array.shape[0]
        self.ncols = self.plot_func_array.shape[1]

        self.param_defs = param_defs
        self.gui_container = template or default_template

        self.sliders = [self.make_slider(par_def, id=id) for id, par_def in enumerate(param_defs)]
        self.plot_output = ipywidgets.Output(
            layout=ipywidgets.Layout(overflow="hidden")
        )

        # Set up figure and initial plot display
        self.fig, self.axes = plt.subplots(
            figsize=(7, 5), nrows=self.nrows, ncols=self.ncols
        )
        self.plot(self.fig, **self.get_param_dict())
        plt.close("all")
        with self.plot_output:
            display(self.fig)

        # Add "Copy parameters to..." and "Save plot to..." UI elements
        self.param_name_field = v.TextField(
            label="Variable name",
            v_model="param_dict",
            small=True,
            style_="max-width:150px",
        )
        self.copy_button = v.Btn(
            children=["Copy params to..."],
            outlined=True,
            small=True,
            style_="margin-right: 20px;",
        )
        self.copy_button.on_event("click", self.copy_parameters_to)

        self.fig_field = v.TextField(
            label="Variable name",
            v_model="fig",
            small=True,
            style_="max-width:150px",
        )
        self.copy_figure_button = v.Btn(
            children=["Copy Figure to..."],
            outlined=True,
            small=True,
            style_="margin-right: 20px;",
        )
        self.copy_figure_button.on_event("click", self.copy_fig_to)

        self.filename_field = v.TextField(
            label="Filename for plot",
            v_model="plot.pdf",
            small=True,
            style_="max-width:150px",
        )
        self.save_button = v.Btn(
            children=["Save figure to..."],
            outlined=True,
            small=True,
            style_="margin-right: 20px;",
        )
        self.save_button.on_event("click", self.save_plot_to)

        self.plot_options_button = v.Btn(
            children=["Plot Options"],
            outlined=True,
            small=True,
            style_="margin-right: 20px;",
        )
        self.plot_options_button.on_event("click", self.show_overlay)

        # Add "Auto Ranges" Checkbox
        self.auto_ranges_checkbox = v.Checkbox(
            v_model=True,  # Default to "on"
            small=True,
            color="primary",
            children=[v.Icon(children=["mdi-check"])],
            style_="margin-right: 20px; margin-left: 40px; margin-top: 0px;",
            label="Auto Ranges"
        )
        self.auto_ranges_checkbox.observe(lambda *args: self.update_plot_display(), names="v_model")
        # Display the interface
        self.control_panel = flex_column(
            [
                flex_row([self.plot_options_button, self.auto_ranges_checkbox]),
                flex_row([self.copy_button, self.param_name_field]),
                flex_row([self.copy_figure_button, self.fig_field]),
                flex_row([self.save_button, self.filename_field]),
            ]
        )

        # Observe slider changes and update plot dynamically
        def handler(*args):
            self.update_plot_display()

        for idx, _ in enumerate(self.param_defs):
            self.sliders[idx].observe(handler, names="v_model")

        self.create_overlay()

        # Display the UI with sliders, plot, and additional buttons/text fields
        display(self.gui_container(self.sliders, self.plot_output, self.control_panel))

    def plot(self, fig: Figure, **kwargs) -> None:
        for idx, plot_func in enumerate(self.plot_func_array.flatten()):
            if plot_func:
                allowed_keys = inspect.signature(plot_func).parameters.keys()
                new_kwargs = {
                    key: val for key, val in kwargs.items() if key in allowed_keys
                }
                plot_func(fig.axes[idx], **new_kwargs)

    def update_plot(self, fig: Figure, *args, **kwargs) -> None:
        for idx, update_plot_func in enumerate(self.update_func_array.flatten()):
            if update_plot_func:
                allowed_keys = inspect.signature(update_plot_func).parameters.keys()
                new_kwargs = {
                    key: val for key, val in kwargs.items() if key in allowed_keys
                }
                update_plot_func(fig.axes[idx], **new_kwargs)

    def copy_parameters_to(self, *args):
        """Copy the parameter dictionary to the specified variable name in the notebook's namespace."""
        param_name = self.param_name_field.v_model or "param_dict"
        param_dict = self.get_param_dict()
        ipython = get_ipython()

        if ipython:
            # Inject the dictionary into the notebook's interactive namespace
            ipython.user_ns[param_name] = param_dict
        else:
            warnings.warn("Warning: Could not access IPython interactive namespace.")

    def copy_fig_to(self, *args):
        """Copy the parameter dictionary to the specified variable name in the notebook's namespace."""
        fig_name = self.fig_field.v_model or "fig"
        ipython = get_ipython()

        if ipython:
            # Inject the dictionary into the notebook's interactive namespace
            ipython.user_ns[fig_name] = self.fig
        else:
            warnings.warn("Warning: Could not access IPython interactive namespace.")

    def save_plot_to(self, *args):
        """Save the current plot to the specified filename."""
        filename = self.filename_field.v_model or "plot.pdf"
        self.fig.savefig(filename)

    def update_plot_display(self):
        """Update the plot display in the Output widget."""
        self.plot_output.clear_output(wait=True)

        auto_ranges = self.auto_ranges_checkbox.v_model

        # Capture existing axis limits
        axis_limits = []
        if not auto_ranges:
            for ax in self.fig.axes:
                axis_limits.append({
                    "xlim": ax.get_xlim(),
                    "ylim": ax.get_ylim()
                })

        # Clear the axes contents without resetting their state
        for ax in self.fig.axes:
            ax.cla()

        # Update the plot with new data
        self.update_plot(self.fig, **self.get_param_dict())

        # Restore axis limits after the plot update
        if not auto_ranges:
            for ax, limits in zip(self.fig.axes, axis_limits):
                ax.set_xlim(*limits["xlim"])
                ax.set_ylim(*limits["ylim"])

        # Redraw the plot
        plt.close("all")
        with self.plot_output:
            display(self.fig)

    @staticmethod
    def make_slider(par_def: ParameterDefinition, id: Optional[int]=-1) -> Union[BaseEntry, DiscreteSetSlider]:
        """
        Takes an arg_range in one of four formats and returns an ipyvuetify element
        appropriate for changing the given parameter.

        Parameters
        ----------
        par_def: Specifies the name of the parameter and its allowed values according
                   to three alternative formats.
                   (i)   (<parameter_name>, <list-like object of allowed values>)
                   (ii)  (<parameter_name>, min, max, step)
                   (iii) (<parameter_name>, min, max, step, ini)

        Returns
        -------
            Slider of the appropriate form. For format (i), this is a DiscreteSetSlider.
            For formats (ii) and (iii) it is a FloatEntry. For (ii) the initial slider
            position is chosen as the midpoint between min and max.

        """
        if len(par_def) == 2:
            var_name, value_list = par_def
            return DiscreteSetSlider(id=id, label=var_name, param_vals=value_list)
        elif len(par_def) == 4:
            var_name, var_min, var_max, step = par_def
            ini = (var_min + var_max) / 2.0
        else:
            var_name, var_min, var_max, step, ini = par_def
        return FloatEntry(
            id=id,
            label=var_name,
            v_model=ini,
            v_min=var_min,
            v_max=var_max,
            step=step,
        )

    def get_param_dict(self) -> dict:
        """
        Return all parameter names and corresponding values as dict.

        Returns
        -------
            A dict of the form `{<param_name>: <param_val>, ...}`
        """
        return {
            par_def[0]: self.sliders[idx].v_model
            for idx, par_def in enumerate(self.param_defs)
        }

    def create_overlay(self):
        """Create the dialog box with text entry fields for figure settings."""
        # Create a text field for figure width
        self.figure_width_entry = v.TextField(
            label="Figure Width",
            v_model=str(self.fig.get_size_inches()[0]),  # Use string to match TextField
            small=True,
        )

        # Create text fields for each Axes
        self.axes_entries = {}
        for idx, ax in enumerate(self.fig.axes):
            entries = {
                "xmin": v.TextField(
                    label="Xmin",
                    v_model=str(ax.get_xlim()[0]),  # Use string to match TextField
                    small=True,
                ),
                "xmax": v.TextField(
                    label="Xmax",
                    v_model=str(ax.get_xlim()[1]),
                    small=True,
                ),
                "ymin": v.TextField(
                    label="Ymin",
                    v_model=str(ax.get_ylim()[0]),
                    small=True,
                ),
                "ymax": v.TextField(
                    label="Ymax",
                    v_model=str(ax.get_ylim()[1]),
                    small=True,
                ),
            }
            self.axes_entries[idx] = entries

        # Create buttons
        apply_button = v.Btn(
            children=["Apply"],
            color="primary",
            small=True,
            style_="margin-right: 10px;",
        )
        close_button = v.Btn(
            children=["Close"],
            color="secondary",
            small=True,
        )

        # Attach actions to buttons
        apply_button.on_event("click", self.apply_settings)
        close_button.on_event("click", self.hide_overlay)

        # Create a dialog box
        self.dialog = v.Dialog(
            v_model=False,
            width="500px",
            children=[
                v.Card(
                    children=[
                        v.CardTitle(children=["Adjust Figure Settings"]),
                        v.CardText(
                            children=[
                                v.Row(
                                    children=[
                                        self.figure_width_entry,
                                    ]
                                )
                            ]
                            + [ flex_column([
                                v.Html(tag='h3', children=[f"Plot #{idx + 1}"]),
                                v.Row(
                                    children=[
                                        entries["xmin"],
                                        entries["xmax"],
                                        entries["ymin"],
                                        entries["ymax"],
                                    ]
                                )])
                                for idx, entries in self.axes_entries.items()
                            ]
                        ),
                        v.CardActions(children=[apply_button, close_button]),
                    ]
                )
            ],
        )
        display(self.dialog)

    def show_overlay(self, *args):
        """Show the overlay dialog."""
        for idx, ax in enumerate(self.fig.axes):
            self.axes_entries[idx]["xmin"].v_model = str(ax.get_xlim()[0])
            self.axes_entries[idx]["xmax"].v_model = str(ax.get_xlim()[1])
            self.axes_entries[idx]["ymin"].v_model = str(ax.get_ylim()[0])
            self.axes_entries[idx]["ymax"].v_model = str(ax.get_ylim()[1])

        self.dialog.v_model = True

    def hide_overlay(self, *args):
        """Hide the overlay dialog."""
        self.dialog.v_model = False

    def apply_settings(self, *args):
        """Apply settings from the dialog to the figure and Axes."""
        try:
            # Convert figure width from string to float
            new_width = float(self.figure_width_entry.v_model)
            _, current_height = self.fig.get_size_inches()

            # Apply figure size
            self.fig.set_size_inches(new_width, current_height)

            # Update Axes limits with string-to-float conversion
            for ax, entries in zip(self.fig.axes, self.axes_entries.values()):
                ax.set_xlim(
                    left=float(entries["xmin"].v_model),
                    right=float(entries["xmax"].v_model),
                )
                ax.set_ylim(
                    bottom=float(entries["ymin"].v_model),
                    top=float(entries["ymax"].v_model),
                )

            self.auto_ranges_checkbox.v_model = False
            # Redraw the plot
            self.update_plot_display()

            # Close the dialog
            self.hide_overlay()

        except ValueError as e:
            # Handle any conversion or input errors
            print(f"Error applying settings: {e}")


class Manipulate(InteractivePlot):
    """
    This class facilitates interactive plotting of a function of multiple parameters,
    in a syntax loosely inspired by Mathematica's `manipulate` function.

    Parameters
    ----------
        func:
            user-provided real-valued function func(z, x1, x2, ...) that depends on one
            variable z (real) and independent parameters x1, x2, ... `Manipulate`
            further accepts an array of such functions to support plotting multiple
            functions. If the array is 1d, plots are arranged in a single column. If the
            array is 2d, plots are arranged in row-major order.
        var_def:
            Specifies the name of the variable z and its values for generating a plot,
            according to two alternative formats:
            (i)   (<parameter_name>, <list-like object of allowed values>)
            (ii)  (<parameter_name>, min, max, step)
        param_defs:
            Specifies the name of the parameter and its allowed values
            according to three alternative formats.
            (i)   (<parameter_name>, <list-like object of allowed values>)
            (ii)  (<parameter_name>, min, max, step)
            (iii) (<parameter_name>, min, max, step, ini)
        template:
            This optional parameter allows user-defined layouts of the user-interface,
            specifically how plot output and sliders are arranged and formatted. The
            default formatting (implemented when this argument is omitted) is governed
            by
            ``def default_template(sliders, plot):
                 return v.Html(tag="div",
                               class_="d-flex flex-row align-start",
                               children=[plot, flex_column(sliders)])``

    """

    def __init__(
        self,
        func: Union[Callable[[numeric, numeric, ...], numeric], np.ndarray, list],
        var_def: VariableDefinition,
        param_defs: ParameterDefinition,
        template: Optional[
            Callable[[List[v.VuetifyWidget], ipywidgets.Output], v.Container]
        ] = default_template,
    ):
        if isinstance(func, list):
            self.funcs = np.array(func)
        elif callable(func):
            self.funcs = np.array([[func]])
        else:
            self.funcs = func
        # func is now expected to be an array, 1d or 2d
        if self.funcs.ndim == 1:
            self.funcs = self.funcs[..., None]  # turn into proper column vector

        if len(var_def) == 2:
            var_name, var_values = var_def
        else:
            var_name, var_min, var_max, var_step = var_def
            num = int((var_max - var_min) / var_step)
            var_values = np.linspace(var_min, var_max, num)

        def create_plot_func(numeric_func) -> callable:
            # Note: we cannot hand an args, kwargs function to InteractivePlot
            # The plot function is expected to reveal the parameters via its signature
            parameters = [
                inspect.Parameter("ax", inspect.Parameter.POSITIONAL_OR_KEYWORD)
            ]
            parameters += [
                inspect.Parameter(param_name, inspect.Parameter.POSITIONAL_OR_KEYWORD)
                for param_name in inspect.signature(numeric_func).parameters.keys()
            ]
            signature = inspect.Signature(parameters)

            func_keys = inspect.signature(numeric_func).parameters.keys()

            def new_plot_func(ax, **kwargs):
                filtered_kwargs = {
                    key: val for key, val in kwargs.items() if key in func_keys
                }
                func_values = np.asarray(
                    [numeric_func(z, **filtered_kwargs) for z in var_values]
                )
                ax.plot(var_values, func_values)

            new_plot_func.__signature__ = signature
            return new_plot_func

        def create_update_func(numeric_func) -> callable:
            # Note: we cannot hand an args, kwargs function to InteractivePlot
            # The plot function is expected to reveal the parameters via its signature
            parameters = [
                inspect.Parameter("ax", inspect.Parameter.POSITIONAL_OR_KEYWORD)
            ]
            parameters += [
                inspect.Parameter(param_name, inspect.Parameter.POSITIONAL_OR_KEYWORD)
                for param_name in inspect.signature(numeric_func).parameters.keys()
            ]
            signature = inspect.Signature(parameters)

            func_keys = inspect.signature(numeric_func).parameters.keys()

            def new_update_func(ax, **kwargs):
                filtered_kwargs = {
                    key: val for key, val in kwargs.items() if key in func_keys
                }
                func_values = np.asarray(
                    [numeric_func(z, **filtered_kwargs) for z in var_values]
                )
                ax.line[0].set_ydata(func_values)

            new_update_func.__signature__ = signature
            return new_update_func

        plot_funcs = np.full_like(self.funcs, None)
        for idx, func in np.ndenumerate(self.funcs):
            if func:
                plot_funcs[idx] = create_plot_func(func)

        super().__init__(
            plot_func=plot_funcs,
            param_defs=param_defs,
            template=template,
        )
