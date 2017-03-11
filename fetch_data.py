# -*- coding: utf-8 -*-
import configparser
import logging
import os
import re
from time import sleep

from selenium import webdriver
from selenium.webdriver.support.select import Select

logging.basicConfig(level=logging.INFO)

CARDS_SELECTOR = '#ddlCard'
ACCOUNTS_CSS_SELECTOR = '#ddlAccounts_m_ddl'
FIRST_ACCOUNT_SELECTOR = '#ctlActivityTable > tbody > tr.item > td:nth-child(1) > a'
account_num_regex = re.compile('\d{3}-\d{6}/\d{2}')
credit_card_regex = re.compile('.* \d{4}')

d = None


def _save_report():
    d.find_element_by_css_selector("#btnDisplay").click()
    d.find_element_by_css_selector("#BTNSAVE").click()
    sleep(0.5)
    d.switch_to_window(d.window_handles[1])
    d.find_element_by_css_selector("#ImgContinue").click()
    d.switch_to_window(d.window_handles[0])


def _go_to_bank_account_view():
    d.find_element_by_css_selector("#navTopImgID_1").click()


def _go_to_credit_account_view():
    d.find_element_by_css_selector("#navTopImgID_2").click()
    d.find_element_by_css_selector(FIRST_ACCOUNT_SELECTOR).click()


def _traverse_all_dropdown_options(css_dropdown_selector, regex):
    # this weird pattern is used since switching windows cause to loose the select dropdown, hence
    # I'm re-selecting it all the time and keeping an index
    i = 0
    while True:
        try:
            account = Select(d.find_element_by_css_selector(css_dropdown_selector)).options[i]
        except IndexError:
            break

        account_name = account.text
        if regex.match(account_name):
            logging.info("Processing account %s", account_name)
            yield account

        i += 1


def _save_accounts(selector, regex):
    for account in _traverse_all_dropdown_options(selector, regex):
        account.click()
        _save_report()


def _save_credit_cards():
    for account in _traverse_all_dropdown_options(ACCOUNTS_CSS_SELECTOR, account_num_regex):
        account.click()
        _save_accounts(CARDS_SELECTOR, credit_card_regex)


def login(id_, pswd):
    d.find_element_by_css_selector(u"a[title=\"כניסה לחשבונך\"]").click()
    d.find_element_by_css_selector(u"#wtr_uid > strong:nth-child(1)").click()
    d.find_element_by_id("uid").send_keys(id_)
    d.find_element_by_css_selector("#wtr_password > strong").click()
    d.find_element_by_id("password").send_keys(pswd)
    d.find_element_by_id("enter").click()


def _retrieve_info(account_id, account_pswd):
    login(account_id, account_pswd)
    logging.info('Fetching checking account')
    _go_to_bank_account_view()
    _save_accounts(ACCOUNTS_CSS_SELECTOR, account_num_regex)

    logging.info('Fetching credit account')
    _go_to_credit_account_view()
    _save_credit_cards()


def get_creds(conf):
    return conf['id'], conf['pswd']


def _get_conf():
    config = configparser.ConfigParser()
    config.read(os.environ['LEUMI_CONFIG'])
    return config


def _create_driver():
    global d
    d = webdriver.Chrome()
    d.implicitly_wait(30)
    d.get("http://www.leumi.co.il/")


def main():
    conf = _get_conf()

    for section, values in conf.items():
        if not values:
            continue
        logging.info('Fetching info for %s bank accounts', section.title())
        _create_driver()
        _retrieve_info(*get_creds(values))
        d.quit()


if __name__ == "__main__":
    main()