#
#    This file is part of suraida.
#
#    Copyright (c) 2024 and later, Jens Koch
#    All rights reserved.
#
#    This source code is licensed under the BSD-style license found in the
#    LICENSE file in the root directory of this source tree.
############################################################################


from typing import Callable, List, Optional, Tuple, Union

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
    FloatEntry,
    BaseEntry,
    DiscreteSetSlider,
)


numeric = Union[int, float, complex, np.number]


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
                children=[plot, flex_column(sliders + [controls])],
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
            user-provided function that can be of two types. (a) If `numerical` is True
            (default), then `plot_func` is expected to have the signature `plot_func(
            the signature `plot_func(fig, ax, x1, x2, ...)`.
            Here, `x1`, `x2`, ... are parameters (those turned into sliders).
            The plot should should be implemented by accessing the matplotlib Figure or
            Axes objects expected as the first two arguments, e.g., `ax.plot(...)`.
            The return value of plot_func is not used.
        param_defs:
            Specifies the name of the parameter and its allowed values
            according to three alternative formats.
            (i)   (<parameter_name>, <list-like object of allowed values>)
            (ii)  (<parameter_name>, min, max, step)
            (iii) (<parameter_name>, min, max, step, ini)
        update_plot_func:
            This is an optional parameter, providing an alternative plotting function
            for updates after the first initial plot. (If omitted, `plot_func` is
            continued to be used for updates.)
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
        plot_func: Callable[
            [plt.Figure, plt.Axes, ...], Optional[Tuple[plt.Figure, plt.Axes]]
        ],
        param_defs: List[
            Union[
                Tuple[str, List[Union[int, float, complex]]],
                Tuple[str, Union[int, float], Union[int, float], Union[int, float]],
                Tuple[
                    str,
                    Union[int, float],
                    Union[int, float],
                    Union[int, float],
                    Union[int, float],
                ],
            ]
        ],
        update_plot_func: Optional[
            Callable[[plt.Figure, plt.Axes, ...], Optional[Tuple[plt.Figure, plt.Axes]]]
        ] = None,
        template: Optional[
            Callable[[List[v.VuetifyWidget], ipywidgets.Output], v.Container]
        ] = None,
    ):
        self.param_defs = param_defs
        self.update_plot = update_plot_func or plot_func
        self.plot = plot_func
        self.gui_container = template or default_template

        self.sliders = [self.make_slider(par_def) for par_def in param_defs]
        self.plot_output = ipywidgets.Output(
            layout=ipywidgets.Layout(overflow="hidden")
        )

        # Set up figure and initial plot display
        self.fig, self.ax = plt.subplots(figsize=(8, 5))
        _ = self.plot(self.fig, self.fig.axes[0], **self.get_param_dict())
        plt.close("all")
        with self.plot_output:
            display(self.fig)

        # Add the "Copy parameters to..." and "Save plot to..." UI elements
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

        # Display the interface
        self.control_panel = flex_column(
            [
                flex_row([self.copy_button, self.param_name_field]),
                flex_row([self.save_button, self.filename_field]),
            ]
        )

        # Observe slider changes and update plot dynamically
        def handler(*args):
            self.update_plot_display()

        for idx, _ in enumerate(self.param_defs):
            self.sliders[idx].observe(handler, names="v_model")

        # Display the UI with sliders, plot, and additional buttons/text fields
        display(self.gui_container(self.sliders, self.plot_output, self.control_panel))

    def copy_parameters_to(self, *args):
        """Copy the parameter dictionary to the specified variable name in the notebook's namespace."""
        param_name = self.param_name_field.v_model or "param_dict"
        param_dict = self.get_param_dict()
        ipython = get_ipython()

        if ipython:
            # Inject the dictionary into the notebook's interactive namespace
            ipython.user_ns[param_name] = param_dict
        else:
            print("Warning: Could not access IPython interactive namespace.")

    def save_plot_to(self, *args):
        """Save the current plot to the specified filename."""
        filename = self.filename_field.v_model or "plot.pdf"
        self.fig.savefig(filename)

    def update_plot_display(self):
        """Update the plot display in the Output widget."""
        self.plot_output.clear_output(wait=True)
        self.fig.axes[0].clear()
        self.update_plot(self.fig, self.fig.axes[0], **self.get_param_dict())
        plt.close("all")
        with self.plot_output:
            display(self.fig)
        self.ax = self.fig.axes[0]

    # def __init__(
    #     self,
    #     plot_func: Callable[[Figure, Axes, ...], Optional[Tuple[Figure, Axes]]],
    #     param_defs: List[
    #         Union[
    #             Tuple[str, List[numeric]],
    #             Tuple[str, numeric, numeric, numeric],
    #             Tuple[str, numeric, numeric, numeric, numeric],
    #         ]
    #     ],
    #     update_plot_func: Optional[
    #         Callable[[Figure, Axes, ...], Optional[Tuple[Figure, Axes]]]
    #     ] = None,
    #     template: Optional[
    #         Callable[[List[v.VuetifyWidget], ipywidgets.Output], v.Container]
    #     ] = default_template,
    # ):
    #     self.param_defs = param_defs
    #     self.update_plot = update_plot_func or plot_func
    #     self.plot = plot_func
    #     self.gui_container = template
    #
    #     self.sliders = [self.make_slider(par_def) for par_def in param_defs]
    #
    #     self.plot_output = ipywidgets.Output(
    #         layout=ipywidgets.Layout(overflow="hidden")
    #     )
    #     self.fig, self.ax = plt.subplots(figsize=(8, 5))
    #     _ = self.plot(self.fig, self.fig.axes[0], **self.get_param_dict())
    #     plt.close("all")
    #     with self.plot_output:
    #         display(self.fig)
    #
    #     def handler(*args):
    #         self.plot_output.clear_output(wait=True)
    #         self.fig.axes[0].clear()
    #         self.update_plot(
    #             self.fig,
    #             self.fig.axes[0],
    #             **self.get_param_dict(),
    #         )
    #         plt.close("all")
    #         with self.plot_output:
    #             display(self.fig)
    #         self.ax = self.fig.axes[0]
    #
    #     for idx, par_def in enumerate(self.param_defs):
    #         self.sliders[idx].observe(handler, names="v_model")
    #
    #     display(self.gui_container(self.sliders, self.plot_output))

    @staticmethod
    def make_slider(
        par_def: Union[
            Tuple[str, Union[List[numeric], np.array]],
            Tuple[str, numeric, numeric, numeric],
            Tuple[str, numeric, numeric, numeric, numeric],
        ]
    ) -> Union[BaseEntry, DiscreteSetSlider]:
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
            position is chosen the midpoint between min and max.

        """
        if len(par_def) == 2:
            var_name, value_list = par_def
            return DiscreteSetSlider(label=var_name, param_vals=value_list)
        elif len(par_def) == 4:
            var_name, var_min, var_max, step = par_def
            ini = (var_min + var_max) / 2.0
        else:
            var_name, var_min, var_max, step, ini = par_def
        return FloatEntry(
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


class Manipulate(InteractivePlot):
    """
    This class facilitates interactive plotting of a function of multiple parameters,
    in a syntax loosely inspired by Mathematica's `manipulate` function.

    Parameters
    ----------
        func:
            user-provided real-valued function func(z, x1, x2, ...) that depends on one
            variable z (real) and independent parameters x1, x2, ...
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
        func: Callable[[numeric, numeric, ...], numeric],
        var_def: Union[
            Tuple[str, List[numeric]],
            Tuple[str, numeric, numeric, numeric],
        ],
        param_defs: List[
            Union[
                Tuple[str, List[numeric]],
                Tuple[str, numeric, numeric],
                Tuple[str, numeric, numeric, numeric],
            ]
        ],
        template: Optional[
            Callable[[List[v.VuetifyWidget], ipywidgets.Output], v.Container]
        ] = default_template,
    ):
        if len(var_def) == 2:
            var_name, var_values = var_def
        else:
            var_name, var_min, var_max, var_step = var_def
            num = int((var_max - var_min) / var_step)
            var_values = np.linspace(var_min, var_max, num)

        def plot_func(fig, ax, **kwargs):
            func_values = np.asarray([func(z, **kwargs) for z in var_values])
            ax.plot(var_values, func_values)

        super().__init__(plot_func=plot_func, param_defs=param_defs, template=template)
