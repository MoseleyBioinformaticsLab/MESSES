from collections import OrderedDict


def create_local_sample_ids(internal_data, internal_section_key='measurement', internal_sample_id_key='sample.id'):
    """Returns a list of the parsed sample IDs from a given dictionary containing experimental analysis data and
    metadata.

    :param internal_data: Dictionary of experimental data from MS or NMR studies
    :param internal_section_key: String identifier for the internal section key. Default: "measurement"
    :param internal_sample_id_key: String identifier for the internal section sample ID key name. Default: "sample.id"
    :type internal_data: :py:class:`collections.OrderedDict` or dict
    :type internal_section_key: str, optional
    :type internal_sample_id_key: str, optional
    :return: List of parsed sample id strings
    :rtype: list
    """
    return list({measurement[internal_sample_id_key] for measurement in internal_data[internal_section_key].values() if measurement[internal_sample_id_key]})


def create_lineages(
        internal_data,
        sample_id,
        section_keys=('sample', 'subject'),
        parent_id_key='parentID',
        protocol_id_key='protocol.id',
        protocol_id='protein_extraction'
):
    """Returns a list of the parsed sample lineages from a given dictionary containing experimental analysis data and
    metadata.

    :param internal_data: Dictionary of experimental data from MS or NMR studies
    :param sample_id: Sample identifier for sample lineage to be created for
    :param section_keys: Tuple of internal sections keys of sections to be parsed for steps in the lineage.
        Default: "("sample", "subject")"
    :param parent_id_key: Key name for parent identifier parameter in internal subject/sample entires. Default:
        "parentID"
    :param protocol_id_key: String identifier for experiment protocol id
    :param protocol_id: Protocol identifier for lineages to be filtered by
    :type internal_data: :py:class:`collections.OrderedDict`
    :type sample_id: str
    :type section_keys: tuple, optional
    :type parent_id_key: str, optional
    :type protocol_id_key: str, optional
    :type protocol_id: str, optional
    :return: List of the parsed sample lineages
    :rtype: list
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
    for parent_id in internal_data['sample'].keys():
        if parent_id not in [lineage_sample['id'] for lineage_sample in lineage_list]:
            if internal_data['sample'][parent_id].get(parent_id_key) == lineage_list[1].get('id') \
                    and protocol_id in internal_data['sample'][parent_id].get(protocol_id_key):
                lineage_list.append(internal_data['sample'][parent_id])

    for parent_id in internal_data["sample"][sample_id].get("protocol.id"):
        if internal_data["protocol"].get(parent_id):
            if internal_data["protocol"][parent_id].get("type") == "storage":
                lineage_list.append({"data_files": internal_data["protocol"][parent_id].get("data_files")})

    return lineage_list


def lineage_to_str(lineage_list):
    """Returns string representation of list of lineage items.

    :param lineage_list: List of sample lineages items
    :type lineage_list: List
    :return: String representation of sample lineages
    :rtype: str
    """
    lineage_str_list = []
    for c, lineage in enumerate(lineage_list):
        for key in lineage.keys():
            if key == 'id':
                lineage_str_list.append('lineage_{}={}'.format(str(c+1), lineage[key]))
            elif key == 'project.id' or key == 'study.id' or key == 'parentID':
                pass
            elif key == "data_files":
                if len(lineage[key]) == 1:
                    lineage_str_list.append('RAW_FILE_NAME={}'.format(str(lineage[key][0])))
                else:
                    lineage_str_list.append('RAW_FILE_NAME={}'.format(str(lineage[key])))
            else:
                lineage_str_list.append('{}={}'.format(str(key), str(lineage[key])))

    return "; ".join(lineage_str_list)


def create_subject_sample_factors_section(
        internal_data,
        subject_type="-",
        internal_section_key="SUBJECT_SAMPLE_FACTORS",
        **kwargs
):
    """Returns ordered dictionary containing items for mwTab SUBJECT_SAMPLE_FACTORS section.

    :param internal_data: Dictionary of experimental data from MS or NMR studies.
    :param subject_type: String representing the subject type. Default: "-"
    :param internal_section_key: String identifier for the internal section key. Default: "SUBJECT_SAMPLE_FACTORS"
    :param kwargs: Dictionary of sample additional data items.
    :type internal_data: :py:class:`collections.OrderedDict`
    :type subject_type: str, optional
    :type internal_section_key: str, optional
    :type kwargs: dict
    :return:
    :rtype: :py:class:`collections.OrderedDict`
    """
    subject_sample_factors = OrderedDict()
    subject_sample_factors[internal_section_key] = []

    sample_ids = create_local_sample_ids(internal_data)

    # create dictionary for each sample
    for sample_id in sample_ids:

        # create top of the lineage (from subject to sample)
        lineage_list = create_lineages(internal_data, sample_id)
        if kwargs.get(sample_id):
            pass

        entry = OrderedDict()
        entry["subject_type"] = subject_type
        entry["local_sample_id"] = sample_id
        entry["factors"] = "{}:{}".format("Treatment Protocol", str(lineage_list[0].get("protocol.id")[0]))
        entry["additional_sample_data"] = lineage_to_str(lineage_list)

        subject_sample_factors[internal_section_key].append(entry)

    return subject_sample_factors


def get_parent(sample_protocol_id, sample_section="sample", subject_section="subject"):
    """Returns identifier for parent of a given sample or protocol.

    :param sample_protocol_id: Sample/protocol identifier for parent sample to be parsed
    :param sample_section: Internal sections keys of sample sections. Default: "sample"
    :param subject_section: Internal sections keys of subject sections. Default: "subject"
    :type sample_protocol_id: str
    :type sample_section: str, optional
    :type subject_section: str, optional
    :return: Sample identifier for parent sample
    :rtype: str
    """
    return sample_section[sample_protocol_id].get("parentID", None) if sample_protocol_id in sample_section else \
        subject_section[sample_protocol_id].get("parentID", None)
