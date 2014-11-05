"""
Functions related to uploading data to REDCap
"""

__author__ = "University of Florida CTS-IT Team"
__copyright__ = "Copyright 2014, University of Florida"
__license__ = "BSD 3-Clause"

import ast
import datetime
import logging
import os
import time

from lxml import etree
from redcap import RedcapError


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

DEFAULT_DATA_DIRECTORY = os.getcwd()


def create_import_data_json(import_data_dict, event_tree):
    """
    create_import_data_json:
    This function converts data in event tree into json format.
    Parameters:
        import_data_dict: This parameter holds the event tree data
        event_tree: This parameter holds the event tree data

    @see #generate_output()
    """

    root = event_tree

    event_name = root.find('name')
    if event_name is None or not event_name.text:
        raise Exception('Expected non-blank element event/name')

    import_data_dict['redcap_event_name'] = event_name.text

    event_field_value_list = root.xpath('//event/field/name')

    for name in event_field_value_list:
        if name.text is None:
            raise Exception(
                'Expected non-blank element event/field/name')

    # Match all fields to build a row for each
    event_field_list = root.xpath('field')
    contains_data = False

    for field in event_field_list:
        val = field.findtext('value', '')
        import_data_dict[field.findtext('name')] = val

        if val and not contains_data:
            contains_data = True

    return {'json_data': import_data_dict, 'contains_data': contains_data}


def generate_output(person_tree, redcap_client, rate_limit, data_repository, skip_blanks=False):
    """
    Note: This function communicates with the redcap application.
    Steps:
        - loop for each person/form/event element
        - generate a csv fragment `using create_eav_output`
        - send csv fragment to REDCap using `send_eav_data_to_redcap`


    @return the report_data dictionary
    """

    # the global dictionary to be returned
    report_data = {
        'errors': []
    }

    """
     For each person we keep a count for each form type:
        subject_details = array(
            'person_A' => array('form_1': 1, 'form_2': 10, ...
            'person_B' => array('form_1': 1, 'form_2': 10, ...
            ...
        )
    """
    subject_details = {}

    # For each form type we keep a global count
    form_details = {}

    # count how many `person` elements are parsed
    person_count = 0

    root = person_tree.getroot()
    persons = root.xpath('//person')

    rate_limiter_value_in_redcap = float(rate_limit)


    ideal_time_per_request = 60 / float(rate_limiter_value_in_redcap)
    time_stamp_after_request = 0

    # main loop for each person
    for person in persons:
        time_begin = datetime.datetime.now()
        person_count += 1
        study_id = (person.xpath('study_id') or [None])[0]

        if study_id is None:
            raise Exception('Expected a valid value for study_id')

        # count how many csv fragments are created per person
        event_count = 0
        logger.info('Start sending data for study_id: %s' % study_id.text)

        forms = person.xpath('./all_form_events/form')

        # loop through the forms of one person
        for form in forms:
            form_name = form.xpath('name')[0].text
            form_key = 'Total_' + form_name + '_Forms'
            study_id_key = study_id.text

            # init dictionary for a new person in (study_id)
            if study_id_key not in subject_details:
                subject_details[study_id_key] = {}
                subject_details[study_id_key]['lab_id'] = person.get('lab_id')

            if not form_key in subject_details[study_id_key]:
                subject_details[study_id_key][form_key] = 0

            if form_key not in form_details:
                form_details[form_key] = 0

            logger.debug(
                'parsing study_id ' +
                study_id.text +
                ' form: ' +
                form_name)

            # loop through the events of one form
            for event in form.xpath('event'):
                event_status = event.findtext('status')
                if event_status == 'sent':
                    continue
                event_count += 1

                try:
                    import_dict = {
                        redcap_client.project.def_field: study_id.text}
                    import_dict = create_import_data_json(
                        import_dict,
                        event)
                    json_data_dict = import_dict['json_data']
                    contains_data = import_dict['contains_data']

                    # If we're skipping blanks and this event is blank, we
                    # assume all following events are blank; therefore, break
                    # out of this for-loop and move on to the next form.
                    if skip_blanks and not contains_data:
                        break

                    time_lapse_since_last_request = time.time(
                    ) - time_stamp_after_request
                    sleepTime = max(
                        ideal_time_per_request -
                        time_lapse_since_last_request,
                        0)
                    # print 'Sleep for: %s seconds' % sleepTime
                    time.sleep(sleepTime)

                    if (0 == event_count % 50):
                        logger.info('Requests sent: %s' % (event_count))

                    # to speedup testing uncomment the following line
                    # if (0 == event_count % 2) : continue

                    try:
                        found_error = False
                        response = redcap_client.send_data_to_redcap([json_data_dict], overwrite = True)
                        status = event.find('status')
                        if status is not None:
                            status.text = 'sent'
                        else:
                            status_element = etree.Element("status")
                            status_element.text = 'sent'
                            event.append(status_element)
                        data_repository.store(person_tree)
                    except RedcapError as e:
                        found_error = handle_errors_in_redcap_xml_response(
                            e.message,
                            report_data)

                    time_stamp_after_request = time.time()

                    if contains_data:
                        if not found_error:
                            # if no errors encountered update event counters
                            subject_details[study_id_key][form_key] += 1
                            form_details[form_key] += 1

                except Exception as e:
                    logger.error(e.message)
                    raise

        time_end = datetime.datetime.now()
        logger.info("Total execution time for study_id %s was %s" % (study_id_key, (time_end - time_begin)))
        logger.info("Total REDCap requests sent: %s \n" % (event_count))

    report_data.update({
        'total_subjects': person_count,
        'form_details': form_details,
        'subject_details': subject_details,
        'errors': report_data['errors']
    })

    logger.debug('report_data ' + repr(report_data))
    return report_data


def handle_errors_in_redcap_xml_response(redcap_response, report_data):
    """
    handle_errors_in_redcap_xml_response:
    This function checks for any errors in the redcap response and update report data if there are any errors.
    Parameters:
        redcap_response_xml: This parameter holds the redcap response passed to this function
        report_data: This parameter holds the report data passed to this function

    """
    # converting string to dictionary
    response = ast.literal_eval(str(redcap_response))
    logger.debug('handling response from the REDCap')
    try:
        if 'error' in response:
            for recordData in response['records']:
                error_string = "Error writing to record " + recordData["record"] + " field " + recordData[
                    "field_name"] + " Value " + recordData["value"] + ".Error Message: " + recordData["message"]
                logger.info(error_string)
                report_data['errors'].append(error_string)
        else:
            logger.error("REDCap response is in unknown format")
    except KeyError as e:
        logger.error(str(e))
    return True
