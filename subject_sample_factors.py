from collections import OrderedDict


def parse_sample_data(internal_data, sample_id):
    """Method for parsing out sample data from a dictionary of internal sample data.

    :param internal_data:
    :param sample_id:
    :return:
    """
    if internal_data['sample'].get(sample_id):
        return internal_data['sample'].get(sample_id)
    elif internal_data['subject'].get(sample_id):
        return internal_data['subject'].get(sample_id)
    else:
        return


def create_lineages(internal_data, sample_id):
    """Method for parsing an dictionary of internal experimental data and creating lineages for a given sample.

    lineage_1=01_A0_T03-2017_naive_UKy_GCH_rep1; protocol.id=['T03-2017_naive']; replicate=1; species=Mus musculus; species_type=Mouse; taxonomy_id=10090;
    lineage_2=01_A0_Colon_T03-2017_naive_170427_UKy_GCH_rep1; protocol.id=['mouse_tissue_collection', 'tissue_quench', 'frozen_tissue_grind'];
    lineage_3=01_A0_Colon_T03-2017_naive_170427_UKy_GCH_rep1-polar-ICMS_A; protocol.id=['polar_extraction', 'ICMS_file_storage46']; replicate=1; replicate%type=analytical; type=cell_extract; weight=0.2521; weight%units=g;
    lineage_4=01_A0_Colon_T03-2017_naive_170427_UKy_GCH_rep1-protein; protein_weight=0.6181768442446792; protein_weight%units=mg; protocol.id=['protein_extraction']

    :param internal_data:
    :param sample_id:
    :return:
    """
    while True:
        pass


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

# def create_subject_sample_factors_section(internal_data, subject_type='-'):
#     subject_sample_factors = OrderedDict()
#     subject_sample_factors['SUBJECT_SAMPLE_FACTORS'] = []
#
#     sample_ids = list({measurement['sample.id'] for measurement in internal_data['measurement']})
#
#     # create dictionary for each sample
#     for sample_id in sample_ids:
#
#         # create top of the lineage (from subject to sample)
#         lineage = create_lineage(internal_data, sample_id)
#
#         entry = OrderedDict()
#         entry['subject_type'] = subject_type
#         entry['local_sample_id'] = sample_id
#         entry['factors'] = factors_str
#         entry['additional_sample_data'] = additional_data_str
#
#     return subject_sample_factors


""" ANDREY'S IMPLEMENTATION """


def create_subject_sample_factors_section(internal_data,
                                          subject_type='-',
                                          mwtab_key='SUBJECT_SAMPLE_FACTORS'):
    subject_sample_factors = OrderedDict()
    subject_sample_factors[mwtab_key] = []  
    
    lineages, sister_lineages = create_lineages(internal_data=internal_data, sister_sample_types=["-protein"])
    sample_factors = create_sample_factors(internal_data=internal_data, lineages=lineages)
    sample_factors_additional_data = create_sample_factors_additional_data(lineages=lineages, sister_lineages=sister_lineages)
    assert list(sample_factors.keys()) == list(sample_factors_additional_data.keys())
    
    for sample_id in sample_factors:
        
        factors_dict = sample_factors[sample_id]
        factors_list_of_str = ['{}:{}'.format(key, value) for key, value in factors_dict.items()]
        factors_str = ' | '.join(factors_list_of_str)
        
        additional_data_list = sample_factors_additional_data[sample_id]
        additional_data_list_of_str = []
        
        for lineage_additional_data_dict in additional_data_list:
            list_of_str = ['{}={}'.format(key, value) for key, value in lineage_additional_data_dict.items()]
            additional_data_list_of_str.extend(list_of_str)
        
        additional_data_str = '; '.join(additional_data_list_of_str)
        
        entry = OrderedDict()
        entry['subject_type'] = subject_type
        entry['local_sample_id'] = sample_id
        entry['factors'] = factors_str
        entry['additional_sample_data'] = additional_data_str
        
        subject_sample_factors[mwtab_key].append(entry)

    return subject_sample_factors


def get_parent(sid, sample_section, subject_section):
    return sample_section[sid].get('parentID', None) if sid in sample_section else subject_section[sid].get('parentID', None) 


def extract_additional_data(sid, section, additional_data_ignore=('id', 'parentID', 'project.id', 'study.id', 'description')):
    additional_data = OrderedDict()
    
    for key, value in section[sid].items():
        if key not in additional_data_ignore:
            additional_data[key] = value
    return additional_data


def create_lineage(terminal_id, sample_section, subject_section):
    lineage = []    
    sid = terminal_id
    section = sample_section if sid in sample_section else subject_section

    while sid:
        lineage_data = OrderedDict()        
        additional_data = extract_additional_data(sid, section)
        lineage_data['lineage_name'] = sid
        lineage_data['additional_data'] = additional_data
        lineage.append(lineage_data)

        sid = get_parent(sid, sample_section, subject_section)
        section = sample_section if sid in sample_section else subject_section
    
    return lineage


def create_sister_samples(terminal_id, sample_section, subject_section, sister_sample_types):
    sister_samples = []
    
    pid = get_parent(terminal_id, sample_section, subject_section)

    for sister_type in sister_sample_types:
        sid = '{}{}'.format(pid, sister_type)
        if sid in sample_section:
            lineage_data = OrderedDict()        
            additional_data = extract_additional_data(sid, sample_section)
            lineage_data['lineage_name'] = sid
            lineage_data['additional_data'] = additional_data
            sister_samples.append(lineage_data)

    return sister_samples


def create_lineages(internal_data, sister_sample_types=None):
    """Method for parsing lineage chains from a given internal data dictionary.

    :param internal_data: Dictionary of experimental data from MS or NMR studies.
    :type internal_data: :py:class:`collections.OrderedDict` or dict
    :param sister_sample_types:
    :return:
    """
    lineages = OrderedDict()
    sister_lineages = OrderedDict()
    sample_section = internal_data['sample']
    subject_section = internal_data['subject']

    local_sample_ids = create_local_sample_ids(internal_data)

    for terminal_id in local_sample_ids:
        lineages[terminal_id] = create_lineage(terminal_id, sample_section, subject_section)
        sister_lineages[terminal_id] = create_sister_samples(terminal_id, sample_section, subject_section, sister_sample_types)

    return lineages, sister_lineages


def extract_factors(section):
    factors = OrderedDict()
    
    for full_factor_name in section.keys():
        if full_factor_name.endswith('replicate'):
            continue
        else:
            parts = full_factor_name.split('.')
            lookup_section_name, *factor_name_parts = parts
            lookup_factor_name = '.'.join(factor_name_parts)
            allowed_values = section[full_factor_name]['allowed_values']
            
            factors[lookup_factor_name] = {'section_name': lookup_section_name,
                                           'factor_name': lookup_factor_name,
                                           'allowed_values': allowed_values}
    return factors


def create_sample_factors(internal_data, lineages):
    sample_factors = OrderedDict()
    factors = extract_factors(section=internal_data['factor'])

    for entry in factors.values():
        factor_name = entry['factor_name']
        section_name = entry['section_name']
        allowed_values = entry['allowed_values']
        section = internal_data[section_name]
        
        for terminal_id, lineage in lineages.items():
            sample_factors.setdefault(terminal_id, OrderedDict())
            
            for lineage_dict in lineage:                
                sid = lineage_dict['lineage_name']
                if sid in section:
                    if factor_name in section[sid] and section[sid][factor_name] in allowed_values:
                        sample_factors[terminal_id][factor_name] = section[sid][factor_name]
                else:
                    continue
    return sample_factors


def create_sample_factors_additional_data(lineages, sister_lineages):
    sample_factors_additional_data = OrderedDict()

    for terminal_id, lineage in lineages.items():
        sample_factors_additional_data.setdefault(terminal_id, [])

        # need to reverse order, because lineages sorted in bottom-to-top order
        for index, lineage_dict in enumerate(reversed(lineage), start=1):
            lineage_id = 'lineage_{}'.format(index)
            lineage_name = lineage_dict['lineage_name']
            additional_data = lineage_dict['additional_data']

            entry = OrderedDict()
            entry[lineage_id] = lineage_name
            entry.update(additional_data)
            sample_factors_additional_data[terminal_id].append(entry)

        for index, lineage_dict in enumerate(sister_lineages[terminal_id], start=1+len(lineage)):
            lineage_id = 'lineage_{}'.format(index)
            lineage_name = lineage_dict['lineage_name']
            additional_data = lineage_dict['additional_data']

            entry = OrderedDict()
            entry[lineage_id] = lineage_name
            entry.update(additional_data)
            sample_factors_additional_data[terminal_id].append(entry)

    return sample_factors_additional_data

