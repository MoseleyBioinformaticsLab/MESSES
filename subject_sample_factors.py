from collections import OrderedDict


def create_local_sample_ids(internal_data, internal_section_key='measurement', internal_sample_id_key='sample.id'):
    """Method for parsing a list of sample ids from a given internal data dictionary.

    :param internal_data: Dictionary of experimental data from MS or NMR studies.
    :type internal_data: :py:class:`collections.OrderedDict` or dict
    :param str internal_section_key:
    :param str internal_sample_id_key:
    :return: List of parsed sample id strings.
    :rtype: list
    """
    return list({measurement[internal_sample_id_key] for measurement in internal_data[internal_section_key].values() if measurement[internal_sample_id_key]})


def create_lineages(
        internal_data,
        sample_id,
        section_keys=['sample', 'subject'],
        parent_id_key='parentID',
        protocol_id_key='protocol.id',
        protocol_id='protein_extraction'
):
    """Method for parsing an dictionary of internal experimental data and creating lineages for a given sample.

    lineage_1=01_A0_T03-2017_naive_UKy_GCH_rep1; protocol.id=['T03-2017_naive']; replicate=1; species=Mus musculus; species_type=Mouse; taxonomy_id=10090;
    lineage_2=01_A0_Colon_T03-2017_naive_170427_UKy_GCH_rep1; protocol.id=['mouse_tissue_collection', 'tissue_quench', 'frozen_tissue_grind'];
    lineage_3=01_A0_Colon_T03-2017_naive_170427_UKy_GCH_rep1-polar-ICMS_A; protocol.id=['polar_extraction', 'ICMS_file_storage46']; replicate=1; replicate%type=analytical; type=cell_extract; weight=0.2521; weight%units=g;
    lineage_4=01_A0_Colon_T03-2017_naive_170427_UKy_GCH_rep1-protein; protein_weight=0.6181768442446792; protein_weight%units=mg; protocol.id=['protein_extraction']

    :param internal_data: Dictionary of experimental data from MS or NMR studies.
    :type internal_data: :py:class:`collections.OrderedDict` or dict
    :param str sample_id: Sample identifier for lineage to be created for.
    :param list section_keys: List of internal sections keys of internal sections to be parsed for steps in the lineage
    (default: ['sample', 'subject']).
    :param str parent_id_key: KEy name for parent identifier parameter in internal subject/sample entires (default:
    'parentID').
    :param str protocol_id_key:
    :return:
    """
    lineage_list = list()

    # create top level sample lineages
    current_id = sample_id
    while True:
        lineage = [internal_data[section].get(current_id) for section in section_keys if internal_data[section].get(current_id)]
        if lineage:
            lineage_list = lineage + lineage_list
            current_id = lineage_list[0].get(parent_id_key)
        else:
            break

    # add additional lineages (sample which do not have measurement information)
    for sample_id in internal_data['sample'].keys():
        if sample_id not in [lineage_sample['id'] for lineage_sample in lineage_list]:
            if any(internal_data['sample'][sample_id].get(parent_id_key) == lineage_sample.get('id') for lineage_sample
                   in lineage_list) and protocol_id in internal_data['sample'][sample_id].get(protocol_id_key):
                lineage_list.append(internal_data['sample'][sample_id])

    return lineage_list


def lineage_to_str(lineage_list):
    """Method for converting a list of lineages items into a string.

    :param lineage_list:
    :return:
    """
    lineage_str_list = []
    for c, lineage in enumerate(lineage_list):
        for key in lineage.keys():
            if key == 'id':
                lineage_str_list.append('lineage_{}={};'.format(str(c+1), lineage[key]))
            elif key == 'project.id' or key == 'study.id' or key == 'parentID':
                pass
            else:
                lineage_str_list.append('{}={};'.format(str(key), str(lineage[key])))

    return " ".join(lineage_str_list)


def create_subject_sample_factors_section(internal_data, subject_type='-', mwtab_key='SUBJECT_SAMPLE_FACTORS'):
    """

    :param internal_data: Dictionary of experimental data from MS or NMR studies.
    :type internal_data: :py:class:`collections.OrderedDict` or dict
    :param str subject_type:
    :param str mwtab_key:
    :return:
    """
    subject_sample_factors = OrderedDict()
    subject_sample_factors[mwtab_key] = []

    sample_ids = create_local_sample_ids(internal_data)

    # create dictionary for each sample
    for sample_id in sample_ids:

        # create top of the lineage (from subject to sample)
        lineage_list = create_lineages(internal_data, sample_id)

        entry = OrderedDict()
        entry['subject_type'] = subject_type
        entry['local_sample_id'] = sample_id
        entry['factors'] = str(lineage_list[0].get('protocol.id')[0])
        entry['additional_sample_data'] = lineage_to_str(lineage_list)

        subject_sample_factors[mwtab_key].append(entry)

    return subject_sample_factors


def get_parent(sid, sample_section, subject_section):
    """

    :param sid:
    :param sample_section:
    :param subject_section:
    :return:
    """
    return sample_section[sid].get('parentID', None) if sid in sample_section else subject_section[sid].get('parentID', None)
