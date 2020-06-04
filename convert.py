"""
Examples:

    # python3 convert.py Exp5_metadata_and_measurements.json MS
    # python3 convert.py Exp5_metadata_and_measurements.json NMR
    # python3 convert.py Exp5_metadata_and_measurements.json NMR NMR1
    # python3 convert.py Exp5_metadata_and_measurements.json NMR NMR2
"""
"""
'factor', 'measurement', 'project', 'protocol', 'sample', 'study', 'subject'

'factor':
{
    "subject.protocol.id": {
        "allowed_values": [
            "T03-2017_naive",
            "T03-2017_syn",
            "T03-2017_allo",
            "T04-2017_syn",
            "T04-2017_allo"
        ],
        "id": "subject.protocol.id",
        "project.id": "GH_Spleen",
        "study.id": "GH_Spleen"
    }
}

'measurement':
{
    (S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCH_rep1-polar-ICMS_A
    {
        "assignment": "(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0",
        "assignment%method": "database",
        "compound": "(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd",
        "corrected_raw_intensity": "8447352.89211",
        "corrected_raw_intensity%type": "natural abundance corrected peak area",
        "formula": "C5H8O4",
        "id": "(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCH_rep1-polar-ICMS_A",
        "injection_volume": "10",
        "injection_volume%units": "uL",
        "isotopologue": "13C0",
        "isotopologue%type": "13C",
        "polar_split_ratio": "0.255757329816374",
        "protein_weight": "0.618176844244679",
        "protein_weight%units": "mg",
        "protocol.id": "ICMS1",
        "raw_intensity": "7989221.83386388",
        "raw_intensity%type": "spectrometer peak area",
        "reconstitution_volume": "20",
        "reconstitution_volume%units": "uL",
        "sample.id": "01_A0_Colon_T03-2017_naive_170427_UKy_GCH_rep1-polar-ICMS_A"
    },
    ...
}

'project':
{
    "GH_Spleen":
    {
        "PI_email": "gerhard.hildebrandt@uky.edu",
        "PI_first_name": "Gerhard",
        "address": "Gerhard C. Hildebrandt, MD, Room no. CC401A, Ben Roach Building, Markey Cancer Center University of Kentucky, Lexington, 40536",
        ...
    }
}

'protocol': {
    "FTMS_file_storage1": {
        "data_files": [
            "Hildebrandt_Spleen01_pos.raw",
            "Hildebrandt_Spleen01_neg.raw"
        ],
        "id": "FTMS_file_storage1",
        "parentID": "file_storage",
        "sample.id": "01_A0_Spleen_T03-2017_naive_170427_UKy_GCH_rep1-lipid",
        "type": "storage"
    },
    ...
}

'sample': {
    "01_A0_Colon_T03-2017_naive_170427_UKy_GCH_rep1": {
        "id": "01_A0_Colon_T03-2017_naive_170427_UKy_GCH_rep1",
        "parentID": "01_A0_T03-2017_naive_UKy_GCH_rep1",
        "project.id": "GH_Spleen",
        "protocol.id": [
            "mouse_tissue_collection",
            "tissue_quench",
            "frozen_tissue_grind"
        ],
        "study.id": "GH_Spleen"
    }, 
    ...
}

'study': {
    "GH_Spleen": {
        "PI_email": "gerhard.hildebrandt@uky.edu",
        "PI_first_name": "Gerhard",
        "PI_last_name": "Hildebrandt",
        "address": "CTW-453, 900 South Limestone street. UKY. Lexington, Kentucky-40536",
        "contact_email": "gerhard.hildebrandt@uky.edu",
        "contact_first_name": "Gerhard",
        ...
    }
}

'subject': {
    "01_A0_T03-2017_naive_UKy_GCH_rep1": {
        "id": "01_A0_T03-2017_naive_UKy_GCH_rep1",
        "project.id": "GH_Spleen",
        "protocol.id": [
            "T03-2017_naive"
        ],
        "replicate": "1",
        "species": "Mus musculus",
        "species_type": "Mouse",
        "study.id": "GH_Spleen",
        "taxonomy_id": "10090"
    },
    ...
}
"""

import sys
import json
import os
from datetime import date
from collections import OrderedDict

import mwtab
import schema_mapping
from subject_sample_factors import create_subject_sample_factors_section
from subject_sample_factors import create_local_sample_ids
from subject_sample_factors import get_parent


def main():
    """Collects commandline arguments and call convert function
    """
    try:
        _, filepath, analysis_type, protocol_id = sys.argv
    except:
        _, filepath, analysis_type, = sys.argv
        protocol_id = None

    convert(internal_data_fpath=filepath, analysis_type=analysis_type, protocol_id=protocol_id)


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

    :param internal_data:
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

            # if internal_field_key == 'phone':
            #     section[mwtab_field_key] = '000-000-0000'

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
        metabolite_name='metabolite_name',
        internal_section_key='measurement',
        units_type_key='corrected_raw_intensity%type',
        assignment='assignment',
        peak_measurement='corrected_raw_intensity',
        sample_id='sample.id',
        protocol_id=None):
    """Method for parsing out metabolite intensity data from an internal dictionary of MS experimental data.

    :param internal_data:
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

    units_key = 'MS_METABOLITE_DATA:UNITS'
    data_start_key = 'MS_METABOLITE_DATA_START'

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
    metabolites_section_key = 'METABOLITES_START' if not extended else 'EXTENDED_METABOLITE_DATA_START'
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
            meta_data_entry[key] = metabolite_entry[key]

        if meta_data_entry not in metabolites[metabolites_section_key]['DATA'] or extended:
            metabolites[metabolites_section_key]['DATA'].append(meta_data_entry)

    return metabolites


def convert(internal_data_fpath, analysis_type, protocol_id=None, results_dir='conversion_results'):
    """Method for converting from internal JSON format to mwtab file format.

    :param str internal_data_fpath: Filepath to data file in internal data format.
    :param str analysis_type: Experimental analysis type of the data file.
    :param str protocol_id: Analysis protocol type of the data file.
    :param str results_dir: Directory for resulting mwtab files to be output into.
    :return:
    """
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    with open(internal_data_fpath, 'r') as infile:
        internal_data = json.load(infile, object_pairs_hook=OrderedDict)

    mwtabfile = OrderedDict()

    # Create Header section
    header_section = create_header()
    mwtab.validator._validate_section(section=header_section, schema=mwtab.mwschema.metabolomics_workbench_schema)
    mwtabfile["METABOLOMICS WORKBENCH"] = header_section

    # Create "PROJECT" section
    project_section = convert_section(
        internal_data=internal_data,
        internal_mapping=schema_mapping.internal_project_section_mapping)
    mwtab.validator._validate_section(section=project_section, schema=mwtab.mwschema.project_schema)
    mwtabfile['PROJECT'] = project_section

    # Convert "STUDY" section
    study_section = convert_section(
        internal_data=internal_data,
        internal_mapping=schema_mapping.internal_study_section_mapping)
    mwtab.validator._validate_section(section=study_section, schema=mwtab.mwschema.study_schema)
    mwtabfile['STUDY'] = study_section

    # Convert "SUBJECT" section
    subject_section = convert_section(
        internal_data=internal_data,
        internal_mapping=schema_mapping.internal_subject_section_mapping)
    mwtab.validator._validate_section(section=subject_section, schema=mwtab.mwschema.subject_schema)
    mwtabfile['SUBJECT'] = subject_section

    # Convert "SUBJECT_SAMPLE_FACTORS" section
    # "SUBJECT_SAMPLE_FACTORS" section is updated later to include factors
    subject_sample_factors_section = create_subject_sample_factors_section(
        internal_data=internal_data,
        subject_type='-',
        mwtab_key='SUBJECT_SAMPLE_FACTORS')
    mwtab.validator._validate_section(section=subject_sample_factors_section, schema=mwtab.mwschema.subject_sample_factors_schema)
    mwtabfile['SUBJECT_SAMPLE_FACTORS'] = subject_sample_factors_section

    # Convert "COLLECTION" section
    collection_section = convert_protocol_section(
        internal_data=internal_data,
        internal_mapping=schema_mapping.internal_collection_section_mapping,
        internal_section_key='protocol',
        internal_section_type='collection',
        protocol_id=collection_protocol_id(internal_data=internal_data))
    mwtab.validator._validate_section(section=collection_section, schema=mwtab.mwschema.collection_schema)
    mwtabfile['COLLECTION'] = collection_section

    # Convert "TREATMENT" section
    treatment_section = convert_protocol_section(
        internal_data=internal_data,
        internal_mapping=schema_mapping.internal_treatment_section_mapping,
        internal_section_key='protocol',
        internal_section_type='treatment')
    mwtab.validator._validate_section(section=treatment_section, schema=mwtab.mwschema.treatment_schema)
    mwtabfile['TREATMENT'] = treatment_section

    # Convert "SAMPLEPREP" section
    sampleprep_section = convert_protocol_section(
        internal_data=internal_data,
        internal_mapping=schema_mapping.internal_sampleprep_section_mapping,
        internal_section_key='protocol',
        internal_section_type='sample_prep')
    mwtab.validator._validate_section(section=sampleprep_section, schema=mwtab.mwschema.sampleprep_schema)
    mwtabfile['SAMPLEPREP'] = sampleprep_section

    # Convert "ANALYSIS" section
    analysis_section = convert_protocol_section(
        internal_data=internal_data,
        internal_mapping=schema_mapping.internal_analysys_section_mapping,
        internal_section_key='protocol',
        internal_section_type=analysis_type,
        protocol_id=protocol_id)
    mwtab.validator._validate_section(section=analysis_section, schema=mwtab.mwschema.analysis_schema)
    mwtabfile['ANALYSIS'] = analysis_section

    # Convert Mass Spec. sections into mwtab format
    # "CHROMATOGRAPHY"
    # "MS"
    # "MS_METABOLITE_DATA"
    # "EXTENDED_METABOLITE_DATA"
    if analysis_type.upper() == 'MS':

        # Convert "CHROMATOGRAPHY" section
        chromatography_section = convert_protocol_section(
            internal_data=internal_data,
            internal_mapping=schema_mapping.internal_chromatography_section_mapping,
            internal_section_key='protocol',
            internal_section_type=analysis_type)
        mwtab.validator._validate_section(section=chromatography_section, schema=mwtab.mwschema.chromatography_schema)
        mwtabfile['CHROMATOGRAPHY'] = chromatography_section

        # Convert "MS" section
        ms_section = convert_protocol_section(
            internal_data=internal_data,
            internal_mapping=schema_mapping.internal_ms_section_mapping,
            internal_section_key='protocol',
            internal_section_type='MS')
        mwtab.validator._validate_section(section=ms_section, schema=mwtab.mwschema.ms_schema)
        mwtabfile['MS'] = ms_section

        # Convert "MS_METABOLITE_DATA" section
        ms_metabolite_data_section = convert_metabolite_data(
            internal_data=internal_data,
            units_type_key='corrected_raw_intensity%type',
            peak_measurement='corrected_raw_intensity',
        )
        mwtabfile['MS_METABOLITE_DATA'] = ms_metabolite_data_section

        # Convert "EXTENDED_METABOLITE_DATA" section
        extended_metabolites_section = convert_metabolites(
            internal_data=internal_data,
            assignment='assignment',
            extended=True,
            raw_intensity='raw_intensity',
            raw_intensity_type='raw_intensity%type')
        mwtabfile['MS_METABOLITE_DATA'].update(extended_metabolites_section)
        mwtab.validator._validate_section(section=ms_metabolite_data_section, schema=mwtab.mwschema.ms_metabolite_data_schema)

        # Convert "METABOLITES" section
        metabolites_section = convert_metabolites(
            internal_data=internal_data,
            assignment='assignment',
            compound='compound',
            isotopologue='isotopologue',
            isotopologue_type='isotopologue%type')
        # mwtab.validator._validate_section(section=metabolites_section, schema=mwtab.mwschema.metabolites_schema)
        mwtabfile['METABOLITES'] = metabolites_section

    # Convert NMR sections into mwtab format
    # "NMR"
    # "NMR_BINNED_DATA"
    elif analysis_type.upper() == 'NMR':

        # Convert "NMR" section
        nmr_section = convert_protocol_section(
            internal_data=internal_data,
            internal_mapping=schema_mapping.internal_nmr_section_mapping,
            internal_section_key='protocol',
            internal_section_type=analysis_type,
            protocol_id=protocol_id)
        mwtab.validator._validate_section(section=nmr_section, schema=mwtab.mwschema.nmr_schema)
        mwtabfile[analysis_type] = nmr_section

        # Convert "NMR_BINNED_DATA" section
        nmr_metabolite_data_section = convert_metabolite_data(
            internal_data=internal_data,
            protocol_id=protocol_id,
            assignment='resonance_assignment',
            units_type_key='intensity%type',
            peak_measurement='intensity')
        mwtabfile['NMR_BINNED_DATA'] = nmr_metabolite_data_section

        # Convert "EXTENDED_NMR_BINNED_DATA" section
        extended_metabolites_section = convert_metabolites(
            internal_data=internal_data,
            assignment='assignment',
            extended=True,
            assignment_lower_bound='assignment_lower_bound',
            assignment_upper_bound='assignment_upper_bound',
            chemical_shift='chemical_shift',
            peak_area='peak_area',
            peak_height='peak_height',
            peak_width='peak_width',
        )
        mwtabfile['NMR_BINNED_DATA'].update(extended_metabolites_section)
        # mwtab.validator._validate_section(section=ms_metabolite_data_section, schema=mwtab.mwschema.ms_metabolite_data_schema)

    else:
        raise ValueError('Unknown analysis type.')

    internal_data_fname = os.path.basename(internal_data_fpath)
    internal_data_fname_parts = internal_data_fname.split('.')

    if internal_data_fname_parts[-1].lower() == 'json':
        internal_data_fname_parts.pop()  # remove extension
        basefname = ''.join(internal_data_fname_parts)
    else:
        basefname = ''.join(internal_data_fname_parts)

    if protocol_id is None:
        protocol_id = ''

    mwtab_json_fpath = os.path.join(results_dir, 'mwtab_{}{}.json'.format(basefname, protocol_id))
    mwtab_txt_fpath = os.path.join(results_dir, 'mwtab_{}{}.txt'.format(basefname, protocol_id))

    with open(mwtab_json_fpath, 'w') as outfile:
        json.dump(mwtabfile, outfile, indent=4)

    with open(mwtab_json_fpath, 'r') as infile, open(mwtab_txt_fpath, 'w') as outfile:
        mwfile = next(mwtab.read_files(mwtab_json_fpath))
        mwfile.write(outfile, file_format="mwtab")


if __name__ == '__main__':
    main()
