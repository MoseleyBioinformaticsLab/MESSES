from collections import OrderedDict
from typing import Optional


def create_local_sample_ids(internal_data: dict|OrderedDict, internal_section_key: str ='measurement', internal_sample_id_key: str ='sample.id') -> list[str]:
    """Returns a list of the parsed sample IDs from a given dictionary containing experimental analysis data and
    metadata.
    
    Args:
        internal_data: Dictionary of experimental data from MS or NMR studies.
        internal_section_key: String identifier for the internal section key. Default: 'measurement'
        internal_sample_id_key: String identifier for the internal section sample ID key name. Default: 'sample.id'
    
    Returns:
        List of parsed sample id strings.
    """
    return list({measurement[internal_sample_id_key] for measurement in internal_data[internal_section_key].values() if measurement[internal_sample_id_key]})


def create_lineages(
        internal_data: OrderedDict,
        sample_id: str,
        section_keys: tuple[str] =('sample', 'subject'),
        parent_id_key: str ='parentID',
        protocol_id_key: str ='protocol.id',
        protocol_id: str ='protein_extraction'
) -> list[dict]:
    """Returns a list of the parsed sample lineages from a given dictionary containing experimental analysis data and
    metadata.

    Args:    
        internal_data: Dictionary of experimental data from MS or NMR studies.
        sample_id: Sample identifier for sample lineage to be created for.
        section_keys: Tuple of internal sections keys of sections to be parsed for steps in the lineage. Default: ('sample', 'subject')
        parent_id_key: Key name for parent identifier parameter in internal subject/sample entires. Default: 'parentID'
        protocol_id_key: String identifier for experiment protocol id. Default: 'protocol.id'
        protocol_id: Protocol identifier for lineages to be filtered by. Default: 'protein_extraction'
    
    Returns:
        List of the parsed sample lineages.
    """
    lineage_list = list()

    # create top level sample lineages
    current_id = sample_id
    while True:
        lineage = [entity_attributes for section in section_keys if (entity_attributes := internal_data[section].get(current_id))]
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

    # adds data_files item at the end of the parsed lineages
    for parent_id in internal_data["sample"][sample_id].get("protocol.id"):
        if internal_data["protocol"].get(parent_id):
            if internal_data["protocol"][parent_id].get("type") == "storage":
                lineage_list.append({"data_files": internal_data["protocol"][parent_id].get("data_files")})

    return lineage_list


def lineage_to_str(lineage_list: list[dict]) -> str:
    """Returns string representation of list of lineage items.

    Args:    
        lineage_list: List of sample lineages items.
    
    Returns:
        String representation of sample lineages.
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
        internal_data: dict,
        subject_type: str ="-",
        internal_section_key: str ="SUBJECT_SAMPLE_FACTORS",
        **kwargs: Optional[dict]
) -> OrderedDict:
    """Returns ordered dictionary containing items for mwTab SUBJECT_SAMPLE_FACTORS section.

    Args
        internal_data: Dictionary of experimental data from MS or NMR studies.
        subject_type: String representing the subject type. Default: "-"
        internal_section_key: String identifier for the internal section key. Default: "SUBJECT_SAMPLE_FACTORS"
        kwargs: Dictionary of sample additional data items.
    
    Returns:
        Subject sample factors section.
    """
    
    ## Are samples guaranteed to have a factor?
    ## Is the closest subject guaranteed to have all factors?
    ## Assuming multiple factors on multiple subjects, how to report subjects? Still use the closest?
    ## Are factors always going to be a field in subjects and samples?
    ## How to determine which siblings need to be added to lineage?
    ## Can "Factors" be a dictionary? What if there are 2 treatment protocols?
    ## Look to see if factor has units and add those to any string.
        
    subject_sample_factors = []
    subject_sample_factors[internal_section_key] = []

    sample_ids = create_local_sample_ids(internal_data)

    # create dictionary for each sample
    for sample_id in sample_ids:

        # create top of the lineage (from subject to sample)
        lineage_list = create_lineages(internal_data, sample_id)
        if kwargs.get(sample_id):
            pass



        # current_id = sample_id
        # parent_id = internal_data["sample"][current_id]["parentID"]
        # closest_subject_id = ""
        # while not closest_subject_id:
        #     if parent_id in internal_data["sample"]:
        #         current_id = parent_id
        #         parent_id = internal_data["sample"][current_id]["parentID"]
        #     elif parent_id in internal_data["subject"]:
        #         closest_subject_id = parent_id



        entry = {}
        # entry["Subject ID"] = closest_subject_id
        # entry["Sample ID"] = sample_id
        # entry["Factors"] = {"Treatment Protocol":str(lineage_list[0].get("protocol.id")[0])}
        
        # entry["Additional sample data"] = {}
        # if "data_files" in lineage_list:
        #     entry["Additional sample data"]["RAW_FILE_NAME"] = str(lineage_list["data_files"])
        
        entry["subject_type"] = subject_type
        entry["local_sample_id"] = sample_id
        entry["factors"] = "{}:{}".format("Treatment Protocol", str(lineage_list[0].get("protocol.id")[0]))
        entry["additional_sample_data"] = lineage_to_str(lineage_list)

        subject_sample_factors.append(entry)

    return subject_sample_factors


def get_parent(sample_protocol_id: str, sample_section: str ="sample", subject_section: str ="subject") -> str:
    """Returns identifier for parent of a given sample or protocol.

    Args:
        sample_protocol_id: Sample/protocol identifier for parent sample to be parsed.
        sample_section: Internal sections keys of sample sections. Default: "sample"
        subject_section: Internal sections keys of subject sections. Default: "subject"
    
    Returns:
        Sample identifier for parent sample.
    """
    return sample_section[sample_protocol_id].get("parentID", None) if sample_protocol_id in sample_section else \
        subject_section[sample_protocol_id].get("parentID", None)
