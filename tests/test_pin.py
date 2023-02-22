#!/usr/bin/env python3

import math
import pytest
import random
from mpllayout import PinBase, RulerPin


################################################################################
# test PinBase __init__()
def test_init_PinBase(): pass


################################################################################
# test PinBase subclasses behavior with dangling pins (parent = None)
def test_dangling_pin():
	pname = "test-pin"
	PinBase(pname, parent=None)
	with pytest.raises(ValueError):
		RulerPin(pname, ruler_pos=random.random())
	with pytest.raises(ValueError):
		RulerPin(pname, ruler_pos=random.random(), parent=None)
	return


################################################################################
# test PinBase subclasses placement-related functions
def _test_placement(pin):
	pin.clear_placement()
	assert pin.is_placed() == False
	pin.set_placement(random.random())
	assert pin.is_placed() == True
	pin.set_placement(None)
	assert pin.is_placed() == False
	pin.set_placement(random.random())
	assert pin.is_placed() == True
	pin.clear_placement()
	assert pin.is_placed() == False
	return


def test_placement_PinBase():
	pref = PinBase("test-pin-ref")
	_test_placement(PinBase("test-pin", parent=None))
	_test_placement(PinBase("test-pin", parent=pref))
	return


def test_placement_RulerPin():
	pref = PinBase("test-pin-ref")
	_test_placement(RulerPin("test-pin", ruler_pos=0, parent=pref))
	return


################################################################################
# test PinBase subclasses placement ref related functions
def _test_placement_ref(pin):
	pref = PinBase("test-pin-ref")
	pin.clear_placement_ref()
	assert pin.is_placeable() == False
	pin.set_placement_ref(pref, offset=random.random())
	assert pin.is_placeable() == True
	pin.set_placement_ref(None, offset=random.random())
	assert pin.is_placeable() == False
	# allow self-reference, we will check this later in circular dependency
	pin.set_placement_ref(pin, offset=random.random())
	assert pin.is_placeable() == True
	pin.clear_placement_ref()
	assert pin.is_placeable() == False
	return


def test_placement_ref_PinBase():
	pref = PinBase("test-pin-ref")
	_test_placement_ref(PinBase("test-pin", parent=None))
	_test_placement_ref(PinBase("test-pin", parent=pref))
	return


def test_placement_ref_RulerPin():
	pref = PinBase("test-pin-ref")
	_test_placement_ref(RulerPin("test-pin", ruler_pos=0, parent=pref))
	return


################################################################################
# test PinBase subclasses get_dependencies()
def test_get_dependencies_PinBase():
	pref = PinBase("test-pin-ref")
	# without parent
	pin = PinBase("test-pin", parent=None)
	pin.clear_placement_ref()
	assert pin.get_dependencies() == tuple()
	pin.set_placement_ref(pref, offset=random.random())
	assert pin.get_dependencies() == (pref, )
	pin.clear_placement_ref()
	assert pin.get_dependencies() == tuple()
	# with parent
	pin = PinBase("test-pin", parent=PinBase("test-pin-parent"))
	pin.clear_placement_ref()
	assert pin.get_dependencies() == tuple()
	pin.set_placement_ref(pref, offset=random.random())
	assert pin.get_dependencies() == (pref, )
	pin.clear_placement_ref()
	assert pin.get_dependencies() == tuple()
	return


def test_get_dependencies_RulerPin():
	pref = PinBase("test-pin-ref")
	ppar = PinBase("test-pin-parent")
	# with parent
	pin = RulerPin("test-pin", ruler_pos=random.random(), parent=ppar)
	pin.clear_placement_ref()
	assert pin.get_dependencies() == (ppar, )
	pin.set_placement_ref(pref, offset=random.random())
	assert pin.get_dependencies() == (pref, )
	pin.clear_placement_ref()
	assert pin.get_dependencies() == (ppar, )
	return


################################################################################
# test PinBase verify_placement()
def test_verify_placement_PinBase():
	pref = PinBase("test-pin-ref")
	pin = PinBase("test-pin")
	for i in range(100):
		pref_pos = random.random()
		offset = random.random()
		pref.set_placement(pref_pos)
		pin.set_placement_ref(pref, offset=offset)
		# unplaced error
		with pytest.raises(PinBase.PlacementError):
			pin.clear_placement()
			pin.verify_placement()
		# invalid placement
		with pytest.raises(PinBase.IncomplyingPlacementError):
			while True:
				pin.set_placement(random.random())
				if not math.isclose(pin.get_placement(), pref_pos + offset):
					break
			pin.verify_placement()
		# valid placement
		pin.set_placement(pref_pos + offset)
		pin.verify_placement()
	return


################################################################################
# test PinBase solve_placement_resursive()
def test_solve_placement_recursive_PinBase():
	for i in range(2, 20):
		pins = list()
		offsets = list()
		for j in range(i):
			pin = PinBase("test-pin-%u" % j)
			offset = random.random()
			if j == 0:
				pin.set_placement(offset)
			else:
				pin.set_placement_ref(pins[j - 1], offset)
			pins.append(pin)
			offsets.append(offset)
		# solve placement
		dep_path = list()
		last_pin = pins[i - 1]
		# check dependency tracking
		last_pin.solve_placement_resursive(dep_path=dep_path)
		assert not dep_path  # should pop'd everything
		# check placement of each pin
		pos = 0.0
		for pin, offset in zip(pins, offsets):
			pin.verify_placement()
			pos += offset
			assert math.isclose(pin.get_placement(), pos)
	return


################################################################################
# test PinBase circular dependency
def _reset_chain_dependency_PinBase(pins: list):
	assert isinstance(pins, list), "must use ordered iterator for this test"
	for i in range(1, len(pins)):
		pins[i].clear_placement()
		pins[i].set_placement_ref(pins[i - 1], random.random())
	return


def test_circular_dependency_PinBase():
	n_pins = 20
	assert n_pins > 0  # this ensures pins[-1] below will always work
	pins = [PinBase("test-pin-%u" % i) for i in range(n_pins)]
	# a chain of pins, reset to P_i <- P_(i+1).
	# if P_i set dependency to any of the pins after it, should cause a circular
	# dependency pattern. the last pin can always be an entry point to detect
	# the ciruclar pattern.
	for i in range(n_pins):
		for j in range(i, n_pins):
			_reset_chain_dependency_PinBase(pins)
			pins[i].set_placement_ref(pins[j], offset=random.random())
			with pytest.raises(PinBase.CircularDependencyError):
				pins[-1].solve_placement_resursive()
	return
