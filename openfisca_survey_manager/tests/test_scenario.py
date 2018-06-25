# -*- coding: utf-8 -*-


import logging

from openfisca_core.model_api import *  # noqa analysis:ignore
from openfisca_core import periods
from openfisca_survey_manager.input_dataframe_generator import (
    make_input_dataframe_by_entity,
    random_data_generator,
    randomly_init_variable,
    )
from openfisca_country_template import CountryTaxBenefitSystem
from openfisca_survey_manager.scenarios import AbstractSurveyScenario


log = logging.getLogger(__name__)


tax_benefit_system = CountryTaxBenefitSystem()


def generate_input_input_dataframe_by_entity(nb_persons, nb_groups, salary_max_value, rent_max_value):
    input_dataframe_by_entity = make_input_dataframe_by_entity(tax_benefit_system, nb_persons, nb_groups)
    randomly_init_variable(
        tax_benefit_system,
        input_dataframe_by_entity,
        'salary',
        max_value = salary_max_value,
        condition = "household_role == 'first_parent'"
        )
    randomly_init_variable(
        tax_benefit_system,
        input_dataframe_by_entity,
        'rent',
        max_value = rent_max_value
        )
    return input_dataframe_by_entity


def test_input_dataframe_generator(nb_persons = 10, nb_groups = 5, salary_max_value = 50000,
        rent_max_value = 1000):
    input_dataframe_by_entity = generate_input_input_dataframe_by_entity(
        nb_persons, nb_groups, salary_max_value, rent_max_value)
    assert (input_dataframe_by_entity['person']['household_role'] == "first_parent").sum() == 5
    assert (input_dataframe_by_entity['person'].loc[
        input_dataframe_by_entity['person']['household_role'] != "first_parent",
        'salary'
        ] == 0).all()

    assert (input_dataframe_by_entity['person'].loc[
        input_dataframe_by_entity['person']['household_role'] == "first_parent",
        'salary'
        ] > 0).all()
    assert (input_dataframe_by_entity['person'].loc[
        input_dataframe_by_entity['person']['household_role'] == "first_parent",
        'salary'
        ] <= salary_max_value).all()

    assert (input_dataframe_by_entity['household']['rent'] > 0).all()
    assert (input_dataframe_by_entity['household']['rent'] < rent_max_value).all()


def test_survey_scenario_input_dataframe_import(nb_persons = 10, nb_groups = 5, salary_max_value = 50000,
        rent_max_value = 1000):

    input_data_frame_by_entity = generate_input_input_dataframe_by_entity(
        nb_persons, nb_groups, salary_max_value, rent_max_value)
    survey_scenario = AbstractSurveyScenario()
    survey_scenario.set_tax_benefit_systems(tax_benefit_system = tax_benefit_system)
    survey_scenario.year = 2017
    survey_scenario.used_as_input_variables = ['salary', 'rent']
    period = periods.period('2017-01')
    data = {
        'input_data_frame_by_entity_by_period': {
            period: input_data_frame_by_entity
            }
        }
    survey_scenario.init_from_data(data = data)

    simulation = survey_scenario.simulation
    assert (
        simulation.calculate('salary', period) == input_data_frame_by_entity['person']['salary']
        ).all()
    assert (
        simulation.calculate('rent', period) == input_data_frame_by_entity['household']['rent']
        ).all()


def test_survey_scenario_input_dataframe_import_scrambled_ids(nb_persons = 10, nb_groups = 5, salary_max_value = 50000,
        rent_max_value = 1000):
    input_data_frame_by_entity = generate_input_input_dataframe_by_entity(
        nb_persons, nb_groups, salary_max_value, rent_max_value)
    input_data_frame_by_entity['person']['household_id'] = 4 - input_data_frame_by_entity['person']['household_id']
    survey_scenario = AbstractSurveyScenario()
    survey_scenario.set_tax_benefit_systems(tax_benefit_system = tax_benefit_system)
    survey_scenario.year = 2017
    survey_scenario.used_as_input_variables = ['salary', 'rent']
    period = periods.period('2017-01')
    data = {
        'input_data_frame_by_entity_by_period': {
            period: input_data_frame_by_entity
            }
        }
    survey_scenario.init_from_data(data = data)
    simulation = survey_scenario.simulation
    period = periods.period('2017-01')
    assert (
        simulation.calculate('salary', period) == input_data_frame_by_entity['person']['salary']
        ).all()
    assert (
        simulation.calculate('rent', period) == input_data_frame_by_entity['household']['rent']
        ).all()


def test_random_data_generator(nb_persons = 10, nb_groups = 5, salary_max_value = 50000,
        rent_max_value = 1000, collection = "test_random_generator"):
    variable_generators_by_period = {
        periods.period('2017-01'): [
            {
                'variable': 'salary',
                'max_value': salary_max_value,
                },
            {
                'variable': 'rent',
                'max_value': rent_max_value,
                }
            ],
        periods.period('2018-01'): [
            {
                'variable': 'salary',
                'max_value': salary_max_value,
                },
            ],
        }
    table_by_entity_by_period = random_data_generator(tax_benefit_system, nb_persons, nb_groups,
        variable_generators_by_period, collection)
    survey_scenario = AbstractSurveyScenario()
    survey_scenario.set_tax_benefit_systems(tax_benefit_system = tax_benefit_system)
    survey_scenario.used_as_input_variables = ['salary', 'rent']
    survey_scenario.year = 2017
    survey_scenario.collection = "test_random_generator"
    data = {
        'input_data_table_by_entity_by_period': table_by_entity_by_period
        }
    survey_scenario.init_from_data(data = data)


if __name__ == "__main__":
    import sys
    log = logging.getLogger(__name__)
    logging.basicConfig(level = logging.DEBUG, stream = sys.stdout)
    test_random_data_generator()
    test_survey_scenario_input_dataframe_import()
    test_survey_scenario_input_dataframe_import_scrambled_ids()