"""
Examples:

    # python3 convert.py Exp5_metadata_and_measurements.json MS
    # python3 convert.py Exp5_metadata_and_measurements.json NMR
    # python3 convert.py Exp5_metadata_and_measurements.json NMR NMR1
    # python3 convert.py Exp5_metadata_and_measurements.json NMR NMR2
"""


import sys
from datetime import date
from collections import OrderedDict

import mwtab
from messes import schema_mapping
from messes.subject_sample_factors import create_subject_sample_factors_section, create_lineages, \
    create_local_sample_ids, get_parent


def create_header(study_id='ST000000', analysis_id='AN000000', created_on=str(date.today()), version='1'):
    """Method for creating fields for converting the internal format to mwtab format.

    :param str study_id: Study id for mwtab file (default: ST000000).
    :param str analysis_id: Analysis id for mwtab file (default: AN000000).
    :param str created_on: Date mwtab file was generated on (default: today's date).
    :param str version: Version of mwtab file (default: 1).
    :return: Dictionary of header items for mwtab format.
    :rtype: :py:class:`collections.OrderedDict`
    """
    mwheader = OrderedDict()
    header = '#METABOLOMICS WORKBENCH STUDY_ID:{} ANALYSIS_ID:{}'.format(study_id, analysis_id)

    mwheader['HEADER'] = header
    mwheader['STUDY_ID'] = study_id
    mwheader['ANALYSIS_ID'] = analysis_id
    mwheader['VERSION'] = version
    mwheader['CREATED_ON'] = created_on
    return mwheader


def convert_section(internal_data, internal_mapping):
    """Method for converting internal project, study, and subject section to respective mwtab section.

    :param internal_data: Dictionary of experimental data from MS or NMR studies.
    :type internal_data: :py:class:`collections.OrderedDict` or dict
    :param internal_mapping:
    :return: mwtab formatted section.
    :rtype: :py:class:`collections.OrderedDict`
    """
    section = OrderedDict()
    internal_section_key = [mapping['internal_section_key'] for mapping in internal_mapping]

    if len(set(internal_section_key)) != 1:
        raise ValueError('"internal_section_key" must be identical.')
    else:
        internal_section_key = internal_section_key[0]

    internal_section = internal_data[internal_section_key]

    for entry_key, entry in internal_section.items():
        for mapping in internal_mapping:
            mwtab_field_key = mapping['mwtab_field_key']
            internal_field_key = mapping['internal_field_key']

            if isinstance(entry.get(internal_field_key), list):
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


def convert_protocol_section(
        internal_data,
        internal_mapping,
        internal_section_key,
        internal_section_type,
        protocol_id=None):
    """Method for converting genertic sections. USed to convert COLLECTION, TREATMENT, SAMPLEPREP, ANALYSIS,
    CHROMATOGRAPHY, MS, and NMR sections.

    :param internal_data: Dictionary of experimental data from MS or NMR studies.
    :type internal_data: :py:class:`collections.OrderedDict` or dict
    :param internal_mapping:
    :param str internal_section_key:
    :param str internal_section_type:
    :param str protocol_id:
    :return:
    """
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


def convert_sample_prep_section(internal_data, internal_section_key='protocol'):
    section = OrderedDict()

    # create lineages to parse protocol IDs from
    sample_ids = create_local_sample_ids(
        internal_data,
        internal_section_key='measurement',
        internal_sample_id_key='sample.id'
    )
    sample_lineages = [create_lineages(internal_data, sample_id) for sample_id in sample_ids]

    # parse protocol IDs
    protocol_ids = set()
    for sample_lineage in sample_lineages:
        for lineage in sample_lineage:
            protocol_ids.update(lineage.get('protocol.id'))

    data = [d for d in internal_data[internal_section_key].items() if d[0] in protocol_ids and d[1].get("type") == "sample_prep"]

    mapping = {
        'SAMPLEPREP_SUMMARY': 'description',
        'SAMPLEPREP_PROTOCOL_ID': 'id',
        'SAMPLEPREP_PROTOCOL_FILENAME': 'filename',
    }
    for m in mapping.items():
        for data_item in data:
            if data_item[1].get(m[1]):
                if m[0] in section:
                    section[m[0]] += '\n{}'.format(data_item[1][m[1]])
                else:
                    section[m[0]] = data_item[1][m[1]]

    return section


def collection_protocol_id(internal_data, protocol_type='collection'):
    """

    :param internal_data:
    :param protocol_type:
    :return:
    """
    sample_ids = create_local_sample_ids(internal_data=internal_data)
    collection_protocol_ids = [protocol for protocol in internal_data["protocol"]
                               if internal_data["protocol"][protocol]["type"] == protocol_type]

    if len(collection_protocol_ids) == 1:
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
                        return protocol_id

            sample_ids = [get_parent(sample_id, internal_data["sample"], internal_data["subject"]) for sample_id in sample_ids]

            if not sample_ids:
                break
    return ''


def convert_metabolite_data(
        internal_data,
        analysis_type,
        metabolite_name='metabolite_name',
        internal_section_key='measurement',
        units_type_key='corrected_raw_intensity%type',
        assignment='assignment',
        peak_measurement='corrected_raw_intensity',
        sample_id='sample.id',
        protocol_id=None):
    """Method for parsing out metabolite intensity data from an internal dictionary of MS experimental data.

    :param internal_data: Dictionary of experimental data from MS or NMR studies.
    :type internal_data: :py:class:`collections.OrderedDict` or dict
    :param metabolite_name:
    :param internal_section_key:
    :param units_type_key:
    :param assignment:
    :param peak_measurement:
    :param sample_id:
    :param protocol_id:
    :return:
    """
    # setup the data dictionary
    metabolite_data = OrderedDict()

    units_key = '{}_METABOLITE_DATA:UNITS'.format(analysis_type.upper())
    data_start_key = '{}_METABOLITE_DATA_START'.format(analysis_type.upper())

    sample_ids = create_local_sample_ids(internal_data=internal_data)
    factors = [str(create_lineages(internal_data, sample)[0].get('protocol.id')[0]) for sample in sample_ids]

    metabolite_data[units_key] = ''
    metabolite_data[data_start_key] = OrderedDict()
    metabolite_data[data_start_key]['Samples'] = sample_ids
    metabolite_data[data_start_key]['Factors'] = factors
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


def convert_metabolites(internal_data, analysis_type, internal_section_key='measurement', assignment='assignment',
                        sample_id_key='sample.id', protocol_id=None, extended=False, **kwargs):
    """Method for parsing metabolite information or extended metabolite data from internal data and converting it to a
    mwtab "METABOLITES" section or "MS_METABOLITE_DATA" block "EXTENDED_METABOLITE_DATA" section respectively.

    :param internal_data:
    :param internal_section_key:
    :param assignment:
    :param protocol_id:
    :param kwargs:
    :return:
    """
    # setup the data dictionary
    metabolites = OrderedDict()
    metabolites_section_key = 'METABOLITES_START' if not extended else 'EXTENDED_{}_METABOLITE_DATA_START'.format(analysis_type.upper())
    metabolites[metabolites_section_key] = OrderedDict()

    # if protocol is not specified - use all measurements data, otherwise filter data based on protocol_id
    if protocol_id is None:
        measurement_data = internal_data[internal_section_key]
    else:
        measurement_data = {k: v for k, v in internal_data[internal_section_key].items()
                            if v['protocol.id'] == protocol_id.upper()}

    measurement_data = sorted(measurement_data.values(), key=lambda entry: (entry[assignment], entry['sample.id']))

    meta_data_keys = [assignment] + sorted(kwargs.values())
    if extended:
        meta_data_keys += [sample_id_key]
    # replaces assignment with 'metabolite_name' and if extended replaces sample_id_key with 'sample_id'
    fields = list()
    for key in meta_data_keys:
        if key == assignment:
            fields.append('metabolite_name')
        elif key == sample_id_key:
            fields.append('sample_id')
        else:
            fields.append(key)
    metabolites[metabolites_section_key]['Fields'] = fields
    metabolites[metabolites_section_key]['DATA'] = []

    for metabolite_entry in measurement_data:
        meta_data_entry = OrderedDict()

        for key in meta_data_keys:
            if key == assignment:
                meta_data_entry['metabolite_name'] = metabolite_entry[key]
            else:
                # if type(metabolite_entry[key]) == list:
                #     meta_data_entry[key] = ','.join(metabolite_entry[key])
                # else:
                meta_data_entry[key] = str(metabolite_entry[key])

        if meta_data_entry not in metabolites[metabolites_section_key]['DATA'] or extended:
            metabolites[metabolites_section_key]['DATA'].append(meta_data_entry)

    return metabolites


def convert(internal_data, analysis_type, protocol_id=None, config_dict={}):
    """Method for converting from internal JSON format to mwtab file format.

    :param internal_data: Filepath to data file in internal data format.
    :type internal_data: dict or :py:class:`collections.OrderedDict`
    :param str analysis_type: Experimental analysis type of the data file.
    :param str protocol_id: Analysis protocol type of the data file.
    :param config_dict:
    :type config_dict: dict or :py:class:`collections.OrderedDict`
    :return:
    """
    mwtabfile = OrderedDict()

    # Create Header section
    header_section = create_header()
    mwtab.validator._validate_section(section=header_section, schema=mwtab.mwschema.metabolomics_workbench_schema)
    mwtabfile["METABOLOMICS WORKBENCH"] = header_section

    # Create "PROJECT" section
    project_section = convert_section(
        internal_data=internal_data,
        internal_mapping=schema_mapping.internal_project_section_mapping
    )
    mwtab.validator._validate_section(section=project_section, schema=mwtab.mwschema.project_schema)
    mwtabfile['PROJECT'] = project_section

    # Convert "STUDY" section
    study_section = convert_section(
        internal_data=internal_data,
        internal_mapping=schema_mapping.internal_study_section_mapping
    )
    mwtab.validator._validate_section(section=study_section, schema=mwtab.mwschema.study_schema)
    mwtabfile['STUDY'] = study_section

    # Convert "SUBJECT" section
    subject_section = convert_section(
        internal_data=internal_data,
        internal_mapping=schema_mapping.internal_subject_section_mapping
    )
    mwtab.validator._validate_section(section=subject_section, schema=mwtab.mwschema.subject_schema)
    mwtabfile['SUBJECT'] = subject_section

    # Convert "SUBJECT_SAMPLE_FACTORS" section
    # "SUBJECT_SAMPLE_FACTORS" section is updated later to include factors
    subject_sample_factors_section = create_subject_sample_factors_section(
        internal_data=internal_data,
        subject_type='-',
        mwtab_key='SUBJECT_SAMPLE_FACTORS'
    )
    mwtab.validator._validate_section(section=subject_sample_factors_section, schema=mwtab.mwschema.subject_sample_factors_schema)
    mwtabfile['SUBJECT_SAMPLE_FACTORS'] = subject_sample_factors_section

    # Convert "COLLECTION" section
    collection_section = convert_protocol_section(
        internal_data=internal_data,
        internal_mapping=schema_mapping.internal_collection_section_mapping,
        internal_section_key='protocol',
        internal_section_type='collection',
        protocol_id=collection_protocol_id(internal_data=internal_data)
    )
    mwtab.validator._validate_section(section=collection_section, schema=mwtab.mwschema.collection_schema)
    mwtabfile['COLLECTION'] = collection_section

    # Convert "TREATMENT" section
    treatment_section = convert_protocol_section(
        internal_data=internal_data,
        internal_mapping=schema_mapping.internal_treatment_section_mapping,
        internal_section_key='protocol',
        internal_section_type='treatment'
    )
    mwtab.validator._validate_section(section=treatment_section, schema=mwtab.mwschema.treatment_schema)
    mwtabfile['TREATMENT'] = treatment_section

    # Convert "SAMPLEPREP" section
    sampleprep_section = convert_sample_prep_section(
        internal_data=internal_data,
    )
    mwtab.validator._validate_section(section=sampleprep_section, schema=mwtab.mwschema.sampleprep_schema)
    mwtabfile['SAMPLEPREP'] = sampleprep_section

    # Convert "ANALYSIS" section
    analysis_section = convert_protocol_section(
        internal_data=internal_data,
        internal_mapping=schema_mapping.internal_analysys_section_mapping,
        internal_section_key='protocol',
        internal_section_type=analysis_type,
        protocol_id=protocol_id
    )
    mwtab.validator._validate_section(section=analysis_section, schema=mwtab.mwschema.analysis_schema)
    mwtabfile['ANALYSIS'] = analysis_section

    # Convert Mass Spec. sections into mwtab format.
    # Sections:
    #     CHROMATOGRAPHY
    #     MS
    #     MS_METABOLITE_DATA
    #     EXTENDED_METABOLITE_DATA
    #     METABOLITES
    if analysis_type.upper() == 'MS':

        # Convert "CHROMATOGRAPHY" section
        # chromatography_section = convert_protocol_section(
        #     internal_data=internal_data,
        #     internal_mapping=schema_mapping.internal_chromatography_section_mapping,
        #     internal_section_key='protocol',
        #     internal_section_type=analysis_type
        # )
        # mwtab.validator._validate_section(section=chromatography_section, schema=mwtab.mwschema.chromatography_schema)
        # mwtabfile['CHROMATOGRAPHY'] = chromatography_section

        # Convert "MS" section
        ms_section = convert_protocol_section(
            internal_data=internal_data,
            internal_mapping=schema_mapping.internal_ms_section_mapping,
            internal_section_key='protocol',
            internal_section_type='MS'
        )
        mwtab.validator._validate_section(section=ms_section, schema=mwtab.mwschema.ms_schema)
        mwtabfile['MS'] = ms_section

        # Convert "MS_METABOLITE_DATA" section
        ms_metabolite_data_section = convert_metabolite_data(
            internal_data=internal_data,
            analysis_type=analysis_type,
            units_type_key='raw_intensity%type',  # 'intensity%type',
            peak_measurement='raw_intensity',  # 'intensity',
        )
        mwtabfile['MS_METABOLITE_DATA'] = ms_metabolite_data_section

        # Convert "EXTENDED_MS_METABOLITE_DATA" section
        extended_metabolites_section = convert_metabolites(
            internal_data=internal_data,
            analysis_type=analysis_type,
            assignment='assignment',
            extended=True,

            # concentration='concentration',
            # concentration_type='concentration%type',
            # concentration_units='concentration%units',
            # normalized_concentration='normalized_concentration',
            # normalized_concentration_type='normalized_concentration%type',
            # normalized_concentration_units='normalized_concentration%units',
            # raw_intensity='raw_intensity',
            # raw_intensity_type='raw_intensity%type',

            assigned_mass='assigned_mass',
            assigned_mass_type='assigned_mass%type',
            assigned_mass_units='assigned_mass%units',
            assignment_scores='assignment_scores',
            expectation_values='expectation_values',
            raw_mz='raw_mz',
            raw_mz_units='raw_mz%units',
            raw_mz_sd='raw_mz_sd',
        )
        mwtabfile['MS_METABOLITE_DATA'].update(extended_metabolites_section)
        mwtab.validator._validate_section(section=mwtabfile['MS_METABOLITE_DATA'], schema=mwtab.mwschema.ms_metabolite_data_schema)

        # Convert "METABOLITES" section
        metabolites_section = convert_metabolites(
            internal_data=internal_data,
            analysis_type=analysis_type,
            assignment='assignment',

            # compound='compound',
            # formula='formula',
            # isotopologue='isotopologue',
            # isotopologue_type='isotopologue%type',

            adduct='adduct',
            adducted_elemental_formula='adducted_elemental_formula',
            adducted_isotopic_formula='adducted_isotopic_formula',
            assignment_type='assignment%type',
            charge='charge',
            elemental_formula='elemental_formula',
            isotopologue='isotopologue',
            isotopologue_type='isotopologue%type',
            natural_abundance_probability='natural_abundance_probability',
        )
        mwtab.validator._validate_section(section=metabolites_section, schema=mwtab.mwschema.metabolites_schema)
        mwtabfile['METABOLITES'] = metabolites_section

    # Convert NMR sections into mwtab format.
    # Sections:
    #   NMR
    #   NMR_BINNED_DATA
    #
    #   -or-
    #
    #   NMR
    #   NMR_METABOLITE_DATA
    #   EXTENDED_NMR_METABOLITE_DATA
    #   METABOLITES
    elif analysis_type.upper() == 'NMR':

        # Convert "NMR" section
        nmr_section = convert_protocol_section(
            internal_data=internal_data,
            internal_mapping=schema_mapping.internal_nmr_section_mapping,
            internal_section_key='protocol',
            internal_section_type=analysis_type,
            protocol_id=protocol_id
        )
        mwtab.validator._validate_section(section=nmr_section, schema=mwtab.mwschema.nmr_schema)
        mwtabfile[analysis_type] = nmr_section

        # Convert "NMR_METABOLITE_DATA" section
        nmr_metabolite_data_section = convert_metabolite_data(
            internal_data=internal_data,
            analysis_type=analysis_type,
            protocol_id=protocol_id,
            assignment='resonance_assignment',
            units_type_key='intensity%type',
            peak_measurement='intensity'
        )
        mwtabfile['NMR_METABOLITE_DATA'] = nmr_metabolite_data_section

        # Convert "EXTENDED_NMR_METABOLITE_DATA" section
        extended_metabolites_section = convert_metabolites(
            internal_data=internal_data,
            analysis_type=analysis_type,
            assignment='resonance_assignment',
            extended=True,
            chemical_shift='chemical_shift',
            peak_area='peak_area',
            peak_height='peak_height',
            peak_width='peak_width',
        )
        mwtabfile['NMR_METABOLITE_DATA'].update(extended_metabolites_section)
        # mwtab.validator._validate_section(section=mwtabfile['NMR_BINNED_DATA'], schema=mwtab.mwschema.nmr_binned_data_schema)

        # Convert "METABOLITES" section
        metabolites_section = convert_metabolites(
            internal_data=internal_data,
            analysis_type=analysis_type,
            assignment='resonance_assignment',
            base_inchi='base_inchi',
            isotopic_inchi='isotopic_inchi',
            peak_description='peak_description',
            peak_pattern='peak_pattern',
            proton_count='proton_count',
            representative_inchi='representative_inchi',
            transient_peak='transient_peak',
            transient_peak_type='transient_peak%type'
        )
        mwtab.validator._validate_section(section=metabolites_section, schema=mwtab.mwschema.metabolites_schema)
        mwtabfile['METABOLITES'] = metabolites_section

    else:
        raise ValueError('Unknown analysis type.')

    return mwtabfile
