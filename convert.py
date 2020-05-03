"""
Examples:

    # python3 convert.py Exp5_metadata_and_measurements.json MS
    # python3 convert.py Exp5_metadata_and_measurements.json NMR
    # python3 convert.py Exp5_metadata_and_measurements.json NMR NMR1
    # python3 convert.py Exp5_metadata_and_measurements.json NMR NMR2
"""

import sys
import json
import os
from datetime import date
from collections import OrderedDict
from collections import defaultdict

import mwtab
import schema_mapping
from subject_sample_factors import create_subject_sample_factors_section
from subject_sample_factors import create_local_sample_ids
from subject_sample_factors import get_parent


def main():
    try:
        _, filepath, analysis_type, protocol_id = sys.argv
    except:
        _, filepath, analysis_type, = sys.argv
        protocol_id = None

    convert(internal_data_fpath=filepath, analysis_type=analysis_type, protocol_id=protocol_id)


def create_header(study_id='ST000000', analysis_id='AN000000', created_on='', version='1'):
    
    mwheader = OrderedDict()
    header = '#METABOLOMICS WORKBENCH STUDY_ID:{} ANALYSIS_ID:{}'.format(study_id, analysis_id)

    if not created_on:
        created_on = str(date.today())

    mwheader['HEADER'] = header
    mwheader['STUDY_ID'] = study_id
    mwheader['ANALYSIS_ID'] = analysis_id
    mwheader['VERSION'] = version
    mwheader['CREATED_ON'] = created_on
    return mwheader


def convert_section(internal_data, internal_mapping):
    section = OrderedDict()

    internal_section_key = [mapping['internal_section_key'] for mapping in internal_mapping]

    if len(set(internal_section_key)) != 1:
        print(internal_section_key)
        raise ValueError('"internal_section_key" must be identical.')
    else:
        internal_section_key = internal_section_key[0]

    internal_section = internal_data[internal_section_key]

    for entry_key, entry in internal_section.items():
        for mapping in internal_mapping:
            mwtab_section_key = mapping['mwtab_section_key']
            internal_section_key = mapping['internal_section_key']
            mwtab_field_key = mapping['mwtab_field_key']
            internal_field_key = mapping['internal_field_key']

            if internal_field_key == 'phone':
                section[mwtab_field_key] = '000-000-0000'

            elif isinstance(entry.get(internal_field_key), list):
                unique_list = []
                for value in entry.get(internal_field_key):
                    if value not in unique_list:
                        unique_list.append(value)
                section[mwtab_field_key] = ', '.join(unique_list)

            elif internal_field_key in entry:
                section[mwtab_field_key] = entry[internal_field_key]

            else:
                continue

    return section


def convert_protocol_section(internal_data, internal_mapping, internal_section_key, internal_section_type, protocol_id=None):

    section = OrderedDict()
    data = [d for d in internal_data[internal_section_key].values() if d['type'] == internal_section_type]

    if protocol_id is not None:
        data = [d for d in data if d['id'] == protocol_id]

    for data_item in data:
        for mapping in internal_mapping:
            mwtab_field_key = mapping.get('mwtab_field_key', '')
            internal_field_key = mapping.get('internal_field_key', '')

            if internal_field_key and data_item.get(internal_field_key, ''):
                if mwtab_field_key in section:
                    section[mwtab_field_key] += '\n{}'.format(data_item[internal_field_key])
                else:
                    section[mwtab_field_key] = data_item[internal_field_key]

            if 'units' in mapping:
                section[mwtab_field_key] = ' '.join([data_item[internal_field_key], data_item[mapping['units']]])
    return section


def collection_protocol_id(internal_data, protocol_type='collection'):
    sample_ids = create_local_sample_ids(internal_data=internal_data)
    collection_protocol_ids = [protocol for protocol in internal_data["protocol"]
                               if internal_data["protocol"][protocol]["type"] == protocol_type]

    if len(collection_protocol_ids) == 1:
        print(collection_protocol_ids[0])
        return collection_protocol_ids[0]

    elif len(collection_protocol_ids) == 0:
        return ''

    else:
        while True:

            for sample_id in sample_ids:
                sample_protocol_ids = internal_data["sample"][sample_id]["protocol.id"]

                if isinstance(sample_protocol_ids, str):
                    sample_protocol_ids = [sample_protocol_ids]

                for protocol_id in sample_protocol_ids:
                    if protocol_id in collection_protocol_ids:
                        print(protocol_id)
                        return protocol_id

            sample_ids = [get_parent(sample_id, internal_data["sample"], internal_data["subject"]) for sample_id in sample_ids]

            if not sample_ids:
                break
    return ''


def convert_metabolite_data(internal_data,
                            analysis_type,
                            metabolite_name='metabolite_name',
                            internal_section_key='measurement',
                            units_type_key='intensity%type',
                            assignment='assignment',
                            peak_measurement='intensity',
                            sample_id='sample.id',
                            protocol_id=None):
    
    # setup the data dictionary
    metabolite_data = OrderedDict()

    units_key = '{}_METABOLITE_DATA:UNITS'.format(analysis_type.upper())
    data_start_key = '{}_METABOLITE_DATA_START'.format(analysis_type.upper())
    sample_ids = create_local_sample_ids(internal_data=internal_data)

    metabolite_data[units_key] = ''
    metabolite_data[data_start_key] = OrderedDict()
    metabolite_data[data_start_key]['Samples'] = sample_ids
    metabolite_data[data_start_key]['Factors'] = []
    metabolite_data[data_start_key]['DATA'] = []

    if protocol_id is None:
        measurement_data = internal_data[internal_section_key]
    else:
        measurement_data = {k: v for k, v in internal_data[internal_section_key].items()
                            if v['protocol.id'] == protocol_id.upper()}

    measurement_data = sorted(measurement_data.values(),
                              key=lambda item: (item[assignment], item[sample_id]))


    units = set()
    measurements_per_metabolite = OrderedDict()

    for metabolite_entry in measurement_data:
        units.add(metabolite_entry[units_type_key])
        metabolite_assignment = metabolite_entry[assignment]
        metabolite_peak_measurement = metabolite_entry[peak_measurement]
        metabolite_sample_id = metabolite_entry[sample_id]

        if metabolite_sample_id not in sample_ids:
            raise ValueError('Unknown "sample.id" in measurement: {}'.format(metabolite_entry))

        measurements_per_metabolite.setdefault(metabolite_assignment, {})
        if metabolite_sample_id in measurements_per_metabolite[metabolite_assignment]:
            raise ValueError('Metabolite "{}" already has value for sample.id "{}"'.format(metabolite_assignment,
                                                                                           metabolite_sample_id))
        else:
            measurements_per_metabolite[metabolite_assignment][metabolite_sample_id] = metabolite_peak_measurement

    if len(units) != 1:
        raise ValueError('Inconsistent units across measurement data: {}.'.format(units))
    else:
        units = list(units)[0]
        metabolite_data[units_key] = units

    for metabolite, measurements in measurements_per_metabolite.items():
        entry = OrderedDict()
        entry[metabolite_name] = metabolite
        for sample_id in sample_ids:
            if sample_id in measurements:
                entry[sample_id] = measurements[sample_id]
            else:
                entry[sample_id] = ''
        metabolite_data[data_start_key]['DATA'].append(entry)

    return metabolite_data


def convert_metabolites(internal_data, internal_section_key='measurement', assignment='assignment',
                        protocol_id=None, extended=False, **kwargs):
    
    # setup the data dictionary
    metabolites = OrderedDict()
    metabolites_section_key = 'EXTENDED_METABOLITE_START' if extended else 'METABOLITES_START'
    metabolites[metabolites_section_key] = OrderedDict()

    # if protocol is not specified - use all measurements data, otherwise filter data based on protocol_id
    if protocol_id is None:
        measurement_data = internal_data[internal_section_key]
    else:
        measurement_data = {k: v for k, v in internal_data[internal_section_key].items()
                            if v['protocol.id'] == protocol_id.upper()}

    measurement_data = sorted(measurement_data.values(),
                              key=lambda entry: (entry[assignment], entry['sample.id']))

    meta_data_keys = [assignment] + sorted(kwargs.values())
    fields = [key if key != assignment else 'metabolite_name' for key in meta_data_keys]
    metabolites[metabolites_section_key]['Fields'] = fields
    metabolites[metabolites_section_key]['DATA'] = []

    for metabolite_entry in measurement_data:
        meta_data_entry = OrderedDict()

        for key in meta_data_keys:
            meta_data_entry[key] = metabolite_entry[key]

        if meta_data_entry not in metabolites[metabolites_section_key]['DATA']:
            metabolites[metabolites_section_key]['DATA'].append(meta_data_entry)

    # TODO: if has the same assignment but different content through a warning, use collections.Counter
    # any(len([entry2 for entry2 in metabolites['METABOLITES_START']['DATA'] if entry2[assignment] == entry1[assignment]]) > 1 for entry1 in  metabolites['METABOLITES_START']['DATA'] )

    return metabolites


def update_factors(mwtabfile, analysis_type, factors_key='SUBJECT_SAMPLE_FACTORS'):
    metabolite_data_key = '{}_METABOLITE_DATA'.format(analysis_type.upper())
    data_start_key = '{}_METABOLITE_DATA_START'.format(analysis_type.upper())

    if factors_key and metabolite_data_key not in mwtabfile:
        raise ValueError('Need to create {} and {}'.format(factors_key, metabolite_data_key))

    factors_list = [ssf['factors'] for ssf in mwtabfile[factors_key][factors_key]]
    mwtabfile[metabolite_data_key][data_start_key]['Factors'] = factors_list


def convert(internal_data_fpath, analysis_type, protocol_id=None, results_dir='conversion_results'):

    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    with open(internal_data_fpath, 'r') as infile:
        internal_data = json.load(infile, object_pairs_hook=OrderedDict)

    mwtabfile = OrderedDict()

    header_section = create_header()
    mwtab.validator.validate_section(section=header_section, schema=mwtab.mwschema.metabolomics_workbench_schema)
    mwtabfile["METABOLOMICS WORKBENCH"] = header_section


    project_section = convert_section(
        internal_data=internal_data,
        internal_mapping=schema_mapping.internal_project_section_mapping)
    mwtab.validator.validate_section(section=project_section, schema=mwtab.mwschema.project_schema)
    mwtabfile['PROJECT'] = project_section


    study_section = convert_section(
        internal_data=internal_data,
        internal_mapping=schema_mapping.internal_study_section_mapping)
    mwtab.validator.validate_section(section=study_section, schema=mwtab.mwschema.study_schema)
    mwtabfile['STUDY'] = study_section


    subject_section = convert_section(
        internal_data=internal_data,
        internal_mapping=schema_mapping.internal_subject_section_mapping)
    mwtab.validator.validate_section(section=subject_section, schema=mwtab.mwschema.subject_schema)
    mwtabfile['SUBJECT'] = subject_section


    subject_sample_factors_section = create_subject_sample_factors_section(
        internal_data=internal_data,
        subject_type='-',
        mwtab_key='SUBJECT_SAMPLE_FACTORS')
    mwtab.validator.validate_section(section=subject_sample_factors_section, schema=mwtab.mwschema.subject_sample_factors_schema)
    mwtabfile['SUBJECT_SAMPLE_FACTORS'] = subject_sample_factors_section


    collection_section = convert_protocol_section(
        internal_data=internal_data,
        internal_mapping=schema_mapping.internal_collection_section_mapping,
        internal_section_key='protocol',
        internal_section_type='collection',
        protocol_id=collection_protocol_id(internal_data=internal_data))
    mwtab.validator.validate_section(section=collection_section, schema=mwtab.mwschema.collection_schema)
    mwtabfile['COLLECTION'] = collection_section


    treatment_section = convert_protocol_section(
        internal_data=internal_data,
        internal_mapping=schema_mapping.internal_treatment_section_mapping,
        internal_section_key='protocol',
        internal_section_type='treatment')
    mwtab.validator.validate_section(section=treatment_section, schema=mwtab.mwschema.treatment_schema)
    mwtabfile['TREATMENT'] = treatment_section


    sampleprep_section = convert_protocol_section(
        internal_data=internal_data,
        internal_mapping=schema_mapping.internal_sampleprep_section_mapping,
        internal_section_key='protocol',
        internal_section_type='sample_prep')
    mwtab.validator.validate_section(section=sampleprep_section, schema=mwtab.mwschema.sampleprep_schema)
    mwtabfile['SAMPLEPREP'] = sampleprep_section


    analysis_section = convert_protocol_section(
        internal_data=internal_data,
        internal_mapping=schema_mapping.internal_analysys_section_mapping,
        internal_section_key='protocol',
        internal_section_type=analysis_type,
        protocol_id=protocol_id)
    mwtab.validator.validate_section(section=analysis_section, schema=mwtab.mwschema.analysis_schema)
    mwtabfile['ANALYSIS'] = analysis_section

    if analysis_type.upper() == 'MS':

        chromatography_section = convert_protocol_section(
            internal_data=internal_data,
            internal_mapping=schema_mapping.internal_chromatography_section_mapping,
            internal_section_key='protocol',
            internal_section_type=analysis_type)
        mwtab.validator.validate_section(section=chromatography_section, schema=mwtab.mwschema.chromatography_schema)
        mwtabfile['CHROMATOGRAPHY'] = chromatography_section

        ms_section = convert_protocol_section(
            internal_data=internal_data,
            internal_mapping=schema_mapping.internal_ms_section_mapping,
            internal_section_key='protocol',
            internal_section_type='MS')
        mwtab.validator.validate_section(section=ms_section, schema=mwtab.mwschema.ms_schema)
        mwtabfile['MS'] = ms_section

        ms_metabolite_data_section = convert_metabolite_data(
            internal_data=internal_data, analysis_type=analysis_type)
        mwtabfile['MS_METABOLITE_DATA'] = ms_metabolite_data_section

        metabolites_section = convert_metabolites(
            internal_data=internal_data,
            assignment='assignment',
            compound='compound',
            isotopologue='isotopologue',
            isotopologue_type='isotopologue%type')
        mwtabfile['METABOLITES'] = metabolites_section

        extended_metabolites_section = convert_metabolites(
            internal_data=internal_data,
            extended=True,
            sample='sample.id',
            assignment='assignment',
            compound='compound',
            isotopologue='isotopologue',
            isotopologue_type='isotopologue%type')
        mwtabfile['EXTENDED_METABOLITE_DATA'] = extended_metabolites_section


    # this is for NMR datasets
    # NMR_METABOLITE_DATA
    #  * Sample
    #  * Factors
    #  * Assignment peaks per sample-factors

    elif analysis_type.upper() == 'NMR':

        nmr_section = convert_protocol_section(
            internal_data=internal_data,
            internal_mapping=schema_mapping.internal_nmr_section_mapping,
            internal_section_key='protocol',
            internal_section_type=analysis_type,
            protocol_id=protocol_id)
        mwtab.validator.validate_section(section=nmr_section, schema=mwtab.mwschema.nmr_schema)
        mwtabfile[analysis_type] = nmr_section

        nmr_metabolite_data_section = convert_metabolite_data(
            internal_data=internal_data,
            analysis_type=analysis_type,
            protocol_id=protocol_id,
            assignment='resonance_assignment')

        mwtabfile['NMR_METABOLITE_DATA'] = nmr_metabolite_data_section

        metabolites_section = convert_metabolites(
            internal_data=internal_data,
            assignment='resonance_assignment',
            base_inchi='base_inchi',
            representative_inchi='representative_inchi',
            isotopic_inchi='isotopic_inchi',
            peak_pattern='peak_pattern',
            proton_count='proton_count',
            transient_peak='transient_peak',
            peak_description='peak_description',
            protocol_id=protocol_id)

        mwtabfile['METABOLITES'] = metabolites_section

        extended_metabolites_section = convert_metabolites(
            internal_data=internal_data,
            extended=True,
            sample_id='sample.id',
            assignment='resonance_assignment',
            chemical_shift='chemical_shift',
            peak_height='peak_height',
            peak_width='peak_width',
            assignment_lower_bound='assignment_lower_bound',
            assignment_upper_bound='assignment_upper_bound',
            protocol_id=protocol_id)
        mwtabfile['EXTENDED_METABOLITE_DATA'] = extended_metabolites_section

    else:
        raise ValueError('Unknown analysis type.')

    update_factors(mwtabfile, analysis_type=analysis_type)
    # mwtab.validator.validate_section(section=ms_metabolite_data_section, schema=mwtab.mwschema.ms_metabolite_data_schema)
    # mwtab.validator.validate_section(section=metabolites_section, schema=mwtab.mwschema.metabolites_schema)

    internal_data_fname = os.path.basename(internal_data_fpath)
    internal_data_fname_parts = internal_data_fname.split('.')

    if internal_data_fname_parts[-1].lower() == 'json':
        internal_data_fname_parts.pop()  # remove extension
        basefname = ''.join(internal_data_fname_parts)
    else:
        basefname = ''.join(internal_data_fname_parts)

    if protocol_id is None:
        protocol_id = ''

    mwtab_json_fname = 'mwtab_{}{}.json'.format(basefname, protocol_id)
    mwtab_txt_fname = 'mwtab_{}{}.txt'.format(basefname, protocol_id)
    mwtab_json_fpath = os.path.join(results_dir, 'mwtab_{}{}.json'.format(basefname, protocol_id))
    mwtab_txt_fpath = os.path.join(results_dir, 'mwtab_{}{}.txt'.format(basefname, protocol_id))

    with open(mwtab_json_fpath, 'w') as outfile:
        json.dump(mwtabfile, outfile, indent=4)

    with open(mwtab_json_fpath, 'r') as infile, open(mwtab_txt_fpath, 'w') as outfile:
        mwfile = next(mwtab.read_files(mwtab_json_fpath))
        mwfile.write(outfile, file_format="mwtab")


if __name__ == '__main__':
    main()
