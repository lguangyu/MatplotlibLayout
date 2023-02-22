#!/usr/bin/env python3

import itertools
import math
import pytest
import random
from mpllayout import PlaceableElementBase, PinBase, LinearRuler


################################################################################
# test each Ruler subclass has correct pin names
def _test_ruler_pin_global_name(ruler):
	rname = ruler.global_name
	for pname in ruler.iter_pin_names():
		ruler.get_pin(pname).global_name == rname + "/" + pname
	return


def test_ruler_pin_global_name_LinearRuler():
	_test_ruler_pin_global_name(LinearRuler("test-ruler"))
	return


################################################################################
# test each Ruler subclass has expected pin ruler_pos
def _test_ruler_pin_ruler_position(ruler, pin_ruler_pos_dict):
	for pname, ruler_pos in pin_ruler_pos_dict.items():
		assert ruler.get_pin(pname).ruler_pos == ruler_pos
	return


def test_ruler_pin_ruler_position_LinearRuler():
	_test_ruler_pin_ruler_position(LinearRuler("test-ruler"),
		{"pmin": 0.0, "pmid": 0.5, "pmax": 1.0})
	return


################################################################################
# test ruler length cannot be negative
def _test_ruler_length_negative(ruler, rlen_value):
	with pytest.raises(ValueError):
		ruler.clear_ruler_length()
		assert ruler.get_ruler_length(allow_calculated=False) is None
		ruler.set_ruler_length(rlen_value)
	return


def test_ruler_length_negative_LinearRuler():
	ruler = LinearRuler("test-ruler")
	_test_ruler_length_negative(ruler, -1)
	for i in range(100):
		_test_ruler_length_negative(ruler, -random.random())
	return


################################################################################
# test each Ruler subclass is_placeable() behavior at init conditions (nothing
# related to placement have been set)
def _test_ruler_placeable_check_init_status(ruler):
	assert ruler.is_placeable() == False
	return


def test_ruler_placeable_check_init_status_LinearRuler():
	_test_ruler_placeable_check_init_status(LinearRuler("test-ruler"))
	return


################################################################################
# test each Ruler subclass is_placeable() behavior when exactly 1 point is
# placed, should be False as no Ruler can be fixed with only 1 point (without
# anything else, including ruler length)
def _test_ruler_placeable_check_1p(ruler):
	ref_pin = PinBase("ref-pin")
	for pin in ruler.iter_pins():
		ruler.clear_placement()
		# check if placement set
		pin.clear_placement()
		pin.clear_placement_ref()
		assert pin.is_placed() == False
		assert pin.is_placeable() == False
		pin.set_placement(random.random())
		assert ruler.is_placeable() == False
		# check if placement ref set
		pin.clear_placement()
		pin.clear_placement_ref()
		assert pin.is_placed() == False
		assert pin.is_placeable() == False
		pin.set_placement_ref(ref_pin, random.random())
		assert ruler.is_placeable() == False
		# clean-up
		pin.clear_placement()
		pin.clear_placement_ref()
		assert pin.is_placed() == False
		assert pin.is_placeable() == False
	return


def test_ruler_placeable_check_1p_LinearRuler():
	_test_ruler_placeable_check_1p(LinearRuler("test-ruler"))
	return


################################################################################
# test each Ruler subclass is_placeable() behavior when certain point positions
# are set
def _test_ruler_manual_placement(ruler, case_list: list, exception=None):
	# if exception set, then expect to raise an exception of certain type
	for c in case_list:
		ruler.clear_placement()
		for pname, figpos in c.items():
			ruler.get_pin(pname).set_placement(figpos)
		if exception is not None:
			with pytest.raises(exception):
				ruler.verify_placement()
		else:
			ruler.verify_placement()
	return


def test_ruler_comply_placement_LinearRuler():
	rn = random.random()
	case_list = [
		{"pmin": 0.0, "pmid": 0.0, "pmax": 0.0},  # all zero
		{"pmin": rn * 1.0, "pmid": rn * 1.0, "pmax": rn * 1.0},  # non-zero, +
		{"pmin": rn * -1., "pmid": rn * -1., "pmax": rn * -1.},  # non-zero, -
		{"pmin": rn * 0.0, "pmid": rn * 1.0, "pmax": rn * 2.0},  # normal
	]
	_test_ruler_manual_placement(LinearRuler("test-ruler"), case_list,
		exception=None)
	return


def test_ruler_incomply_placement_LinearRuler():
	rn = random.random()
	case_list = [
		{"pmin": rn * 0.0, "pmid": rn * -1., "pmax": rn * -2.},  # pmax < pmin
		{"pmin": rn * 0.0, "pmid": rn * 1.5, "pmax": rn * 2.0},  # pmid too large
		{"pmin": rn * 0.0, "pmid": rn * 0.5, "pmax": rn * 2.0},  # pmid too small
	]
	_test_ruler_manual_placement(LinearRuler("test-ruler"), case_list,
		exception=PlaceableElementBase.IncomplyingPlacementError)
	return


################################################################################
# test LinearRuler subclass placement using two fixed points
def test_linear_ruler_local_two_point_placement():
	name = "test-ruler"
	r = LinearRuler(name)
	pnames = ["pmin", "pmid", "pmax"]
	rulpos = [r.get_pin(p).ruler_pos for p in pnames]
	n_pnames = len(pnames)
	for i in range(n_pnames):
		for j in range(i + 1, n_pnames):
			assert i < j
			r.clear_placement()
			assert r.get_ruler_length(allow_calculated=False) is None
			pi = r.get_pin(pnames[i])
			pj = r.get_pin(pnames[j])
			pi.set_placement(1.0)
			pj.set_placement(2.0)
			# check value with manual calculation
			rlen = (pi.get_placement() - pj.get_placement())\
				/ (rulpos[i] - rulpos[j])
			assert math.isclose(rlen, r.calc_ruler_length())
			r.solve_placement()
			for k in filter(lambda x: x not in (i, j), range(n_pnames)):
				pk = r.get_pin(pnames[k])
				expect = pi.get_placement() + (rulpos[k] - rulpos[i]) * rlen
				assert math.isclose(pk.get_placement(), expect)
	return


################################################################################
# test LinearRuler invalid placement verification
def test_verify_placement_LinearRuler():
	# test only for the verification of *LinearRuler* only conditions, not those
	# for pins
	ruler = LinearRuler("test-ruler")
	# this should be successful case
	ruler.clear_placement()
	ruler.pmin_pin.set_placement(0.0)
	ruler.pmid_pin.set_placement(1.0)
	ruler.pmax_pin.set_placement(2.0)
	ruler.solve_placement_resursive()
	ruler.verify_placement()
	# test pmid is not exactly the mid-point between pmin and pmax
	with pytest.raises(PlaceableElementBase.IncomplyingPlacementError):
		ruler.clear_placement()
		ruler.pmin_pin.set_placement(0.0)
		ruler.pmid_pin.set_placement(1.1)
		ruler.pmax_pin.set_placement(2.0)
		ruler.solve_placement_resursive()
		ruler.verify_placement()
	# test pmid > pmax
	with pytest.raises(PlaceableElementBase.IncomplyingPlacementError):
		ruler.clear_placement()
		ruler.pmin_pin.set_placement(2.0)
		ruler.pmid_pin.set_placement(1.0)
		ruler.pmax_pin.set_placement(0.0)
		ruler.solve_placement_resursive()
		ruler.verify_placement()
	return


################################################################################
# test external dependency on non-reference pins of LinearRuler
# this test does not test if the test pin can be placed at the correct position,
# but only if the dependency resolution is correct and exception-free
# NOTE: position test should be done above in 2p or pl placement tests
def _test_non_reference_pin_dependency_LinearRuler_2p(ruler, pn1, pn2, pnt):
	assert pn1 != pn2, "pn1 must be different than pn2"
	assert pnt not in (pn1, pn2), "for this test, the pin referenced by an "\
		"external pin cannot be either p1 or p2 specified here"
	ruler.clear_placement()
	# ensure p1.ruler_pos < p2.ruler_pos
	p1 = ruler.get_pin(pn1)
	p2 = ruler.get_pin(pn2)
	if p1.ruler_pos > p2.ruler_pos:
		p1, p2 = p2, p1
	# set p1, p2 placements
	p1_pos = random.random()
	p1.set_placement(p1_pos)
	p2.set_placement(p1_pos + random.random())
	# create test pin
	test_pin = PinBase("test-pin")
	test_pin.set_placement_ref(ruler.get_pin(pnt), offset=random.random())
	test_pin.solve_placement_resursive()
	return


def _test_non_reference_pin_dependency_LinearRuler_pl(ruler, pn, rlen, pnt):
	assert pn != pnt, "the reference pn must be different than test pin (pnt)"
	ruler.clear_placement()
	# set pn placements and ruler length
	ruler.get_pin(pn).set_placement(random.random())
	ruler.set_ruler_length(rlen)
	# create test pin
	test_pin = PinBase("test-pin")
	test_pin.set_placement_ref(ruler.get_pin(pnt), offset=random.random())
	test_pin.solve_placement_resursive()
	return


def test_non_reference_pin_dependency_LinearRuler():
	ruler = LinearRuler("test-ruler")
	pnames = ["pmin", "pmid", "pmax"]
	n_pnames = len(pnames)
	for i in range(n_pnames):
		for j in range(i + 1, n_pnames):
			pn1, pn2 = pnames[i], pnames[j]
			pnt = pnames[3 - i - j]
			_test_non_reference_pin_dependency_LinearRuler_2p(ruler,
				pn1, pn2, pnt)
	for i, j in itertools.product(range(n_pnames), repeat=2):
		if i == j:
			continue
		_test_non_reference_pin_dependency_LinearRuler_pl(ruler,
			pnames[i], random.random(), pnames[j])
	return
