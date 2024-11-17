#
#    This file is part of suraida.
#
#    Copyright (c) 2024 and later, Jens Koch
#    All rights reserved.
#
#    This source code is licensed under the BSD-style license found in the
#    LICENSE file in the root directory of this source tree.
############################################################################


from typing import List, Optional, Union

import ipyvuetify as v
import numpy as np
import traitlets


numeric = Union[int, float, complex, np.number]


class BaseEntry(v.Container):
    def __init__(
        self,
        label: str,
        v_model: Optional[int | float | np.number],
        v_min: int | float | np.number,
        v_max: int | float | np.number,
        step: int | float | np.number,
        text_kwargs=None,
        slider_kwargs=None,
        container_kwargs=None,
        id=-1,
    ):
        self.add_traits(v_model=traitlets.Float(v_model).tag(sync=True))
        self.add_traits(id=traitlets.Int(id).tag(sync=True))
        text_kwargs = {"style_": "max-width: 50px;"} | (text_kwargs or {})
        slider_kwargs = slider_kwargs or {}
        container_kwargs = container_kwargs or {}
        container_kwargs = {
            "class_": "d-flex flex-row",
            "style_": "max-width: 240px;",
        } | container_kwargs

        # Initialize range attributes
        self.v_min = v_min
        self.v_max = v_max

        # Create TextField and Slider with initial values, not traitlets
        self.text_field = v.TextField(
            label=label, v_model=v_model, dense=True, **text_kwargs
        )
        self.slider = v.Slider(
            min=self.v_min,
            max=self.v_max,
            step=step,
            v_model=v_model,
            thumb_label=True,
            **slider_kwargs,
        )

        super().__init__(
            children=[self.text_field, self.slider],
            **container_kwargs,
        )
        self.v_model = v_model
        self.id = id

        # Link changes to central v_model
        self.text_field.on_event("focusout", self._on_text_field_focusout)
        self.slider.observe(self._on_slider_change, names="v_model")
        self.observe(self._on_v_model_change, names="v_model")

    def _on_text_field_focusout(self, widget, event, data):
        """Validate and set precise value from TextField on focusout."""
        try:
            new_value = self.convert_to_type(self.text_field.v_model)
            if self.v_min <= new_value <= self.v_max:
                self.v_model = new_value
            else:
                self.text_field.v_model = self.v_model  # Revert if out of range
        except ValueError:
            self.text_field.v_model = self.v_model  # Revert if input is invalid

    def _on_slider_change(self, change):
        """Update v_model when slider changes."""
        if change["new"] != self.v_model:
            self.v_model = change["new"]

    def _on_v_model_change(self, change):
        """Sync TextField and Slider with the new v_model value."""
        new_value = change["new"]
        if self.text_field.v_model != new_value:
            self.text_field.v_model = new_value
        if self.slider.v_model != new_value:
            self.slider.v_model = new_value

    def convert_to_type(self, value):
        """Convert input to the correct type (float or int)."""
        raise NotImplementedError("Subclasses must implement convert_to_type.")


class FloatEntry(BaseEntry, traitlets.HasTraits):
    def __init__(
        self,
        label: str,
        v_model,
        v_min: int | float | np.number,
        v_max: int | float | np.number,
        step: int | float | np.number,
        text_kwargs=None,
        slider_kwargs=None,
        container_kwargs=None,
        id=-1,
    ):
        super().__init__(
            label=label,
            v_model=v_model,
            v_min=v_min,
            v_max=v_max,
            step=step,
            text_kwargs=text_kwargs,
            slider_kwargs=slider_kwargs,
            container_kwargs=container_kwargs,
            id=id,
        )

    def convert_to_type(self, value):
        return float(value)  # Ensure the value is a float


class IntEntry(BaseEntry, traitlets.HasTraits):
    def __init__(
        self,
        label: str,
        v_model: Optional[int],
        v_min: int,
        v_max: int,
        step: int,
        text_kwargs=None,
        slider_kwargs=None,
        container_kwargs=None,
        id=-1,
    ):
        super().__init__(
            label=label,
            v_model=v_model,
            v_min=v_min,
            v_max=v_max,
            step=step,
            text_kwargs=text_kwargs,
            slider_kwargs=slider_kwargs,
            container_kwargs=container_kwargs,
            id=id,
        )

    def convert_to_type(self, value):
        return int(value)  # Ensure the value is an integer


class DiscreteSetSlider(v.Container, traitlets.HasTraits):
    def __init__(
        self,
        label: str,
        param_vals: List[numeric] | np.ndarray,
        initial_index=0,
        slider_kwargs=None,
        container_kwargs=None,
        id=-1,
    ):
        slider_kwargs = slider_kwargs or {}
        container_kwargs = container_kwargs or {}
        container_kwargs = {
            "class_": "d-flex flex-column",
            "style_": "max-width: 240px;",
        } | container_kwargs

        # Store the parameter values and set the initial index
        self.label = label
        self.param_vals = (
            np.array(param_vals) if isinstance(param_vals, list) else param_vals
        )
        self.val_count = len(param_vals)

        # Set up v_model as a traitlet to represent the value, allowing any numeric type
        self.add_traits(v_model=traitlets.Any(param_vals[initial_index]).tag(sync=True))
        self.v_model = param_vals[initial_index]

        # Create the slider with initial index and display label
        self.slider = v.Slider(
            min=0,
            max=self.val_count - 1,
            step=1,
            v_model=initial_index,
            thumb_label=False,
            **slider_kwargs,
        )

        # Initialize the display label
        self.label_display = v.Html(
            tag="span", children=[f"{self.label}: {self.current_value()}"]
        )

        # Set up the container
        super().__init__(
            id=str(id), children=[self.label_display, self.slider], **container_kwargs
        )

        # Observe changes in the slider and the trait
        self.slider.observe(self._on_slider_change, names="v_model")
        self.observe(self._on_v_model_change, names="v_model")

    def _on_slider_change(self, change):
        """Update v_model to the corresponding value in param_vals when the slider changes."""
        new_index = change["new"]
        if 0 <= new_index < self.val_count:
            new_value = self.param_vals[new_index]
            if new_value != self.v_model:
                self.v_model = new_value

    def _on_v_model_change(self, change):
        """Update the slider and label display when v_model changes."""
        new_value = change["new"]
        if new_value in self.param_vals:
            new_index = np.where(self.param_vals == new_value)[0]
            # Sync the slider's v_model
            if self.slider.v_model != new_index:
                self.slider.v_model = new_index
            # Update label display with the current parameter value
            self.label_display.children = [f"{self.label}: {self.current_value()}"]

    def current_value(self):
        """Return the actual value stored in v_model."""
        return self.v_model


def flex_column(widgets: List[v.VuetifyWidget], class_="", **kwargs) -> v.Container:
    return v.Container(
        class_="d-flex flex-column " + class_, children=widgets, **kwargs
    )


def flex_row(widgets: List[v.VuetifyWidget], class_="", **kwargs) -> v.Container:
    return v.Container(class_="d-flex flex-row " + class_, children=widgets, **kwargs)
