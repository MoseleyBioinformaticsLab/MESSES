# -*- coding: utf-8 -*-
"""
conversion tags for the mwtab format
"""

import copy


ms_tags = \
{
  "ANALYSIS": {
    "ANALYSIS_TYPE": {
      "id": "ANALYSIS_TYPE",
      "override": "MS",
      "value_type": "str"
    }
  },
  "CHROMATOGRAPHY": {
    "CHROMATOGRAPHY_SUMMARY": {
      "fields": [
        "chromatography_description"
      ],
      "id": "CHROMATOGRAPHY_SUMMARY",
      "required": "False",
      "table": "protocol",
      "test": "type=MS",
      "value_type": "str"
    },
    "CHROMATOGRAPHY_TYPE": {
      "fields": [
        "chromatography_type"
      ],
      "id": "CHROMATOGRAPHY_TYPE",
      "required": "True",
      "table": "protocol",
      "test": "type=MS",
      "value_type": "str"
    },
    "COLUMN_NAME": {
      "fields": [
        "column_name"
      ],
      "id": "COLUMN_NAME",
      "required": "True",
      "table": "protocol",
      "test": "type=MS",
      "value_type": "str"
    },
    "INSTRUMENT_NAME": {
      "fields": [
        "chromatography_instrument_name"
      ],
      "id": "INSTRUMENT_NAME",
      "required": "True",
      "table": "protocol",
      "test": "type=MS",
      "value_type": "str"
    }
  },
  "COLLECTION": {
    "COLLECTION_PROTOCOL_FILENAME": {
      "fields": [
        "filename"
      ],
      "id": "COLLECTION_PROTOCOL_FILENAME",
      "required": "False",
      "table": "protocol",
      "test": "type=collection",
      "value_type": "str"
    },
    "COLLECTION_PROTOCOL_ID": {
      "fields": [
        "id"
      ],
      "id": "COLLECTION_PROTOCOL_ID",
      "required": "True",
      "table": "protocol",
      "test": "type=collection",
      "value_type": "str"
    },
    "COLLECTION_SUMMARY": {
      "fields": [
        "description"
      ],
      "id": "COLLECTION_SUMMARY",
      "required": "True",
      "table": "protocol",
      "test": "type=collection",
      "value_type": "str"
    },
    "SAMPLE_TYPE": {
      "fields": [
        "sample_type"
      ],
      "id": "SAMPLE_TYPE",
      "required": "True",
      "table": "protocol",
      "test": "type=collection",
      "value_type": "str"
    }
  },
  "METABOLOMICS WORKBENCH": {
    "ANALYSIS_ID": {
      "id": "ANALYSIS_ID",
      "override": "AN000000",
      "value_type": "str"
    },
    "CREATED_ON": {
      "code": "str(datetime.datetime.now().date())",
      "id": "CREATED_ON",
      "value_type": "str"
    },
    "STUDY_ID": {
      "id": "STUDY_ID",
      "override": "ST000000",
      "value_type": "str"
    },
    "VERSION": {
      "id": "VERSION",
      "override": "1",
      "value_type": "str"
    }
  },
  "MS": {
    "INSTRUMENT_NAME": {
      "fields": [
        "instrument"
      ],
      "id": "INSTRUMENT_NAME",
      "required": "True",
      "table": "protocol",
      "test": "type=MS",
      "value_type": "str"
    },
    "INSTRUMENT_TYPE": {
      "fields": [
        "instrument_type"
      ],
      "id": "INSTRUMENT_TYPE",
      "required": "True",
      "table": "protocol",
      "test": "type=MS",
      "value_type": "str"
    },
    "ION_MODE": {
      "fields": [
        "ion_mode"
      ],
      "id": "ION_MODE",
      "required": "True",
      "table": "protocol",
      "test": "type=MS",
      "value_type": "str"
    },
    "MS_COMMENTS": {
      "fields": [
        "description"
      ],
      "id": "MS_COMMENTS",
      "required": "False",
      "table": "protocol",
      "test": "type=MS",
      "value_type": "str"
    },
    "MS_TYPE": {
      "fields": [
        "ionization"
      ],
      "id": "MS_TYPE",
      "required": "True",
      "table": "protocol",
      "test": "type=MS",
      "value_type": "str"
    }
  },
  "MS_METABOLITE_DATA": {
    "Data": {
      "collate": "assignment",
      "headers": [
        "\"Metabolite\"=assignment",
        "sample.id=intensity"
      ],
      "id": "Data",
      "sort_by": [
        "assignment"
      ],
      "sort_order": "ascending",
      "table": "measurement",
      "value_type": "matrix"
    },
    "Extended": {
      "exclusion_headers": [
        "id",
        "intensity",
        "intensity%type",
        "intensity%units",
        "assignment",
        "sample.id",
        "formula",
        "compound",
        "isotopologue",
        "isotopologue%type"
      ],
      "fields_to_headers": "True",
      "headers": [
        "\"Metabolite\"=assignment",
        "\"sample_id\"=sample.id"
      ],
      "id": "Extended",
      "sort_by": [
        "assignment"
      ],
      "sort_order": "ascending",
      "table": "measurement",
      "value_type": "matrix",
      "values_to_str": "True"
    },
    "Metabolites": {
      "collate": "assignment",
      "headers": [
        "\"Metabolite\"=assignment",
        "\"formula\"=formula",
        "\"compound\"=compound",
        "\"isotopologue\"=isotopologue",
        "\"isotopologue%type\"=isotopologue%type"
      ],
      "id": "Metabolites",
      "sort_by": [
        "assignment"
      ],
      "sort_order": "ascending",
      "table": "measurement",
      "value_type": "matrix"
    },
    "Units": {
      "fields": [
        "intensity%type"
      ],
      "id": "Units",
      "table": "measurement",
      "value_type": "str"
    }
  },
  "PROJECT": {
    "ADDRESS": {
      "fields": [
        "address"
      ],
      "id": "ADDRESS",
      "table": "project",
      "value_type": "str"
    },
    "DEPARTMENT": {
      "fields": [
        "department"
      ],
      "id": "DEPARTMENT",
      "table": "project",
      "value_type": "str"
    },
    "EMAIL": {
      "fields": [
        "PI_email"
      ],
      "id": "EMAIL",
      "table": "project",
      "value_type": "str"
    },
    "FIRST_NAME": {
      "fields": [
        "PI_first_name"
      ],
      "id": "FIRST_NAME",
      "table": "project",
      "value_type": "str"
    },
    "INSTITUTE": {
      "fields": [
        "institution"
      ],
      "id": "INSTITUTE",
      "table": "project",
      "value_type": "str"
    },
    "LAST_NAME": {
      "fields": [
        "PI_last_name"
      ],
      "id": "LAST_NAME",
      "table": "project",
      "value_type": "str"
    },
    "PHONE": {
      "fields": [
        "phone"
      ],
      "id": "PHONE",
      "table": "project",
      "value_type": "str"
    },
    "PROJECT_SUMMARY": {
      "fields": [
        "description"
      ],
      "id": "PROJECT_SUMMARY",
      "table": "project",
      "value_type": "str"
    },
    "PROJECT_TITLE": {
      "fields": [
        "title"
      ],
      "id": "PROJECT_TITLE",
      "table": "project",
      "value_type": "str"
    }
  },
  "SAMPLEPREP": {
    "SAMPLEPREP_PROTOCOL_FILENAME": {
      "delimiter": ";",
      "fields": [
        "filename"
      ],
      "for_each": "True",
      "id": "SAMPLEPREP_PROTOCOL_FILENAME",
      "required": "False",
      "sort_by": [
        "id"
      ],
      "sort_order": "ascending",
      "table": "protocol",
      "test": "type=treatment",
      "value_type": "str"
    },
    "SAMPLEPREP_PROTOCOL_ID": {
      "delimiter": ";",
      "fields": [
        "id"
      ],
      "for_each": "True",
      "id": "SAMPLEPREP_PROTOCOL_ID",
      "required": "True",
      "sort_by": [
        "id"
      ],
      "sort_order": "ascending",
      "table": "protocol",
      "test": "type=sample_prep",
      "value_type": "str"
    },
    "SAMPLEPREP_SUMMARY": {
      "delimiter": "\" \"",
      "fields": [
        "description"
      ],
      "for_each": "True",
      "id": "SAMPLEPREP_SUMMARY",
      "required": "True",
      "sort_by": [
        "id"
      ],
      "sort_order": "ascending",
      "table": "protocol",
      "test": "type=sample_prep",
      "value_type": "str"
    }
  },
  "STUDY": {
    "ADDRESS": {
      "fields": [
        "address"
      ],
      "id": "ADDRESS",
      "table": "study",
      "value_type": "str"
    },
    "DEPARTMENT": {
      "fields": [
        "department"
      ],
      "id": "DEPARTMENT",
      "table": "study",
      "value_type": "str"
    },
    "EMAIL": {
      "fields": [
        "PI_email"
      ],
      "id": "EMAIL",
      "table": "study",
      "value_type": "str"
    },
    "FIRST_NAME": {
      "fields": [
        "PI_first_name"
      ],
      "id": "FIRST_NAME",
      "table": "study",
      "value_type": "str"
    },
    "INSTITUTE": {
      "fields": [
        "institution"
      ],
      "id": "INSTITUTE",
      "table": "study",
      "value_type": "str"
    },
    "LAST_NAME": {
      "fields": [
        "PI_last_name"
      ],
      "id": "LAST_NAME",
      "table": "study",
      "value_type": "str"
    },
    "PHONE": {
      "fields": [
        "phone"
      ],
      "id": "PHONE",
      "table": "study",
      "value_type": "str"
    },
    "STUDY_SUMMARY": {
      "fields": [
        "description"
      ],
      "id": "STUDY_SUMMARY",
      "table": "study",
      "value_type": "str"
    },
    "STUDY_TITLE": {
      "fields": [
        "title"
      ],
      "id": "STUDY_TITLE",
      "table": "study",
      "value_type": "str"
    }
  },
  "SUBJECT": {
    "SUBJECT_SPECIES": {
      "fields": [
        "species"
      ],
      "id": "SUBJECT_SPECIES",
      "table": "entity",
      "test": "type=subject",
      "value_type": "str"
    },
    "SUBJECT_TYPE": {
      "fields": [
        "species_type"
      ],
      "id": "SUBJECT_TYPE",
      "table": "entity",
      "test": "type=subject",
      "value_type": "str"
    },
    "TAXONOMY_ID": {
      "fields": [
        "taxonomy_id"
      ],
      "id": "TAXONOMY_ID",
      "table": "entity",
      "test": "type=subject",
      "value_type": "str"
    }
  },
  "SUBJECT_SAMPLE_FACTORS": {
    "no_id_needed": {
      "code": "mwtab_tag_functions.create_subject_sample_factors(input_json)",
      "id": "no_id_needed",
      "value_type": "section"
    }
  },
  "TREATMENT": {
    "TREATMENT_PROTOCOL_FILENAME": {
      "delimiter": ";",
      "fields": [
        "filename"
      ],
      "for_each": "True",
      "id": "TREATMENT_PROTOCOL_FILENAME",
      "required": "False",
      "sort_by": [
        "id"
      ],
      "sort_order": "ascending",
      "table": "protocol",
      "test": "type=treatment",
      "value_type": "str"
    },
    "TREATMENT_PROTOCOL_ID": {
      "delimiter": ";",
      "fields": [
        "id"
      ],
      "for_each": "True",
      "id": "TREATMENT_PROTOCOL_ID",
      "required": "True",
      "sort_by": [
        "id"
      ],
      "sort_order": "ascending",
      "table": "protocol",
      "test": "type=treatment",
      "value_type": "str"
    },
    "TREATMENT_SUMMARY": {
      "delimiter": "\" \"",
      "fields": [
        "description"
      ],
      "for_each": "True",
      "id": "TREATMENT_SUMMARY",
      "required": "True",
      "sort_by": [
        "id"
      ],
      "sort_order": "ascending",
      "table": "protocol",
      "test": "type=treatment",
      "value_type": "str"
    }
  }
}



nmr_tags = copy.deepcopy(ms_tags)
del nmr_tags["CHROMATOGRAPHY"]
del nmr_tags["MS"]
del nmr_tags["MS_METABOLITE_DATA"]

nmr_tags["ANALYSIS"]["ANALYSIS_TYPE"]["override"] = "NM"
nmr_tags["NM"] = {
    "ACQUISITION_TIME": {
      "fields": [
        "acquisition_time",
        "\" \"",
        "acquisition_time%units"
      ],
      "id": "ACQUISITION_TIME",
      "required": "False",
      "table": "protocol",
      "test": "type=NMR",
      "value_type": "str"
    },
    "BASELINE_CORRECTION_METHOD": {
      "fields": [
        "baseline_correction_method"
      ],
      "id": "BASELINE_CORRECTION_METHOD",
      "required": "False",
      "table": "protocol",
      "test": "type=NMR",
      "value_type": "str"
    },
    "CHEMICAL_SHIFT_REF_CPD": {
      "fields": [
        "chemical_shift_ref_cpd"
      ],
      "id": "CHEMICAL_SHIFT_REF_CPD",
      "required": "False",
      "table": "protocol",
      "test": "type=NMR",
      "value_type": "str"
    },
    "INSTRUMENT_NAME": {
      "fields": [
        "instrument"
      ],
      "id": "INSTRUMENT_NAME",
      "required": "True",
      "table": "protocol",
      "test": "type=NMR",
      "value_type": "str"
    },
    "INSTRUMENT_TYPE": {
      "fields": [
        "instrument_type"
      ],
      "id": "INSTRUMENT_TYPE",
      "required": "True",
      "table": "protocol",
      "test": "type=NMR",
      "value_type": "str"
    },
    "NMR_EXPERIMENT_TYPE": {
      "fields": [
        "NMR_experiment_type"
      ],
      "id": "NMR_EXPERIMENT_TYPE",
      "required": "True",
      "table": "protocol",
      "test": "type=NMR",
      "value_type": "str"
    },
    "NMR_PROBE": {
      "fields": [
        "NMR_probe"
      ],
      "id": "NMR_PROBE",
      "required": "False",
      "table": "protocol",
      "test": "type=NMR",
      "value_type": "str"
    },
    "NMR_SOLVENT": {
      "fields": [
        "NMR_solvent"
      ],
      "id": "NMR_SOLVENT",
      "required": "False",
      "table": "protocol",
      "test": "type=NMR",
      "value_type": "str"
    },
    "NMR_TUBE_SIZE": {
      "fields": [
        "NMR_tube_size",
        "\" \"",
        "NMR_tube_size%units"
      ],
      "id": "NMR_TUBE_SIZE",
      "required": "False",
      "table": "protocol",
      "test": "type=NMR",
      "value_type": "str"
    },
    "PULSE_SEQUENCE": {
      "fields": [
        "pulse_sequence"
      ],
      "id": "PULSE_SEQUENCE",
      "required": "False",
      "table": "protocol",
      "test": "type=NMR",
      "value_type": "str"
    },
    "RELAXATION_DELAY": {
      "fields": [
        "relaxation_delay",
        "\" \"",
        "relaxation_delay%units"
      ],
      "id": "RELAXATION_DELAY",
      "required": "False",
      "table": "protocol",
      "test": "type=NMR",
      "value_type": "str"
    },
    "SHIMMING_METHOD": {
      "fields": [
        "shimming_method"
      ],
      "id": "SHIMMING_METHOD",
      "required": "False",
      "table": "protocol",
      "test": "type=NMR",
      "value_type": "str"
    },
    "SPECTROMETER_FREQUENCY": {
      "fields": [
        "spectrometer_frequency",
        "\" \"",
        "spectrometer_frequency%units"
      ],
      "id": "SPECTROMETER_FREQUENCY",
      "required": "True",
      "table": "protocol",
      "test": "type=NMR",
      "value_type": "str"
    },
    "STANDARD_CONCENTRATION": {
      "fields": [
        "standard_concentration",
        "\" \"",
        "standard_concentration%units"
      ],
      "id": "STANDARD_CONCENTRATION",
      "required": "False",
      "table": "protocol",
      "test": "type=NMR",
      "value_type": "str"
    },
    "TEMPERATURE": {
      "fields": [
        "temperature",
        "\" \"",
        "temperature%units"
      ],
      "id": "TEMPERATURE",
      "required": "False",
      "table": "protocol",
      "test": "type=NMR",
      "value_type": "str"
    },
    "WATER_SUPPRESSION": {
      "fields": [
        "water_suppression"
      ],
      "id": "WATER_SUPPRESSION",
      "required": "False",
      "table": "protocol",
      "test": "type=NMR",
      "value_type": "str"
    }
  }

nmr_tags["NMR_METABOLITE_DATA"] = {
    "Data": {
      "collate": "resonance_assignment",
      "headers": [
        "\"Metabolite\"=resonance_assignment",
        "sample.id=intensity"
      ],
      "id": "Data",
      "sort_by": [
        "resonance_assignment"
      ],
      "sort_order": "ascending",
      "table": "measurement",
      "value_type": "matrix",
      "values_to_str": "True"
    },
    "Extended": {
      "exclusion_headers": [
        "id",
        "intensity",
        "intensity%type",
        "intensity%units",
        "resonance_assignment",
        "sample.id",
        "base_inchi",
        "representative_inchi",
        "isotopic_inchi",
        "peak_description",
        "peak_pattern",
        "proton_count",
        "transient_peak",
        "transient_peak%type"
      ],
      "fields_to_headers": "True",
      "headers": [
        "\"Metabolite\"=resonance_assignment",
        "\"sample_id\"=sample.id"
      ],
      "id": "Extended",
      "sort_by": [
        "resonance_assignment"
      ],
      "sort_order": "ascending",
      "table": "measurement",
      "value_type": "matrix",
      "values_to_str": "True"
    },
    "Metabolites": {
      "collate": "resonance_assignment",
      "headers": [
        "\"Metabolite\"=resonance_assignment",
        "\"base_inchi\"=base_inchi",
        "\"representative_inchi\"=representative_inchi",
        "\"isotopic_inchi\"=isotopic_inchi",
        "\"peak_description\"=peak_description",
        "\"peak_pattern\"=peak_pattern",
        "\"proton_count\"=proton_count",
        "\"transient_peak\"=transient_peak",
        "\"transient_peak_type\"=transient_peak%type"
      ],
      "id": "Metabolites",
      "sort_by": [
        "resonance_assignment"
      ],
      "sort_order": "ascending",
      "table": "measurement",
      "value_type": "matrix",
      "values_to_str": "True"
    },
    "Units": {
      "fields": [
        "intensity%type"
      ],
      "id": "Units",
      "table": "measurement",
      "value_type": "str"
    }
  }

nmr_binned_tags = copy.deepcopy(nmr_tags)
del nmr_binned_tags["NMR_METABOLITE_DATA"]
nmr_binned_tags["NMR_BINNED_DATA"] = {
    "Data": {
      "collate": "assignment",
      "headers": [
        "\"Bin range(ppm)\"=assignment",
        "sample.id=intensity"
      ],
      "id": "Data",
      "sort_by": [
        "assignment"
      ],
      "sort_order": "ascending",
      "table": "measurement",
      "value_type": "matrix"
    },
    "Units": {
      "fields": [
        "intensity%type"
      ],
      "id": "Units",
      "table": "measurement",
      "value_type": "str"
    }
  }
