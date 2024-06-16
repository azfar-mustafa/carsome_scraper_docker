import requests
from bs4 import BeautifulSoup
import logging
import time
import csv
import datetime
from requests.exceptions import HTTPError
import sys

logging.basicConfig(filename='scraping.log', 
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def get_html(page_number: int = None) -> BeautifulSoup:
    """
    Get car data from website.

    Args:
        page_number (int, optional): The page number to fetch. Defaults to None.

    Returns:
        BeautifulSoup: Parsed HTML page as a BeautifulSoup object.
    """
    header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'}

    if page_number is not None:
        url = f"https://www.carsome.my/buy-car/perodua/myvi?pageNo={page_number}"
    else:
        url = "https://www.carsome.my/buy-car/perodua/myvi"

    try:
        response = requests.get(url, headers=header)
        response.raise_for_status()
        logging.info(f"Opening webpage {url}") 
    except HTTPError as http_err:
        logging.error(f"HTTP error occured: {http_err}")
        sys.exit(1) # This will stop the program immediately if there is http error
    
    car_html = BeautifulSoup(response.text, 'html.parser')
    return car_html


def get_page_number_list(car_html: BeautifulSoup) -> list[int]:
    """
    Get list of webpage number.

    Args:
        car_html Beautifulsoup: The webpage of car data.

    Returns:
        list[int]: List of webpage number.
    """
    page_numbers = []
    page_number = car_html.find_all('li', class_='mod-pagination__item')
    for item in page_number:
        button = item.find('button')
        if button and button.text.isdigit():
            page_numbers.append(int(button.text))
    return page_numbers


def get_max_page_number(page_number_list: list[int]) -> int:
    """
    Get the maximum number of webpage.

    Args:
        page_number_list list[int]: List of webpage number.

    Returns:
        int: Maximum webpage number.
    """
    max_number = max(page_number_list) if page_number_list else 1
    logging.info(f"Max page number is {max_number}")
    return max_number


def get_car_list(car_webpage: BeautifulSoup) -> BeautifulSoup:
    """
    Get all car in advertisement.

    Args:
        car_data BeautifulSoup: Contain car advertisement per webpage.

    Returns:
        BeautifulSoup: Return car advertisement details.
    """
    car_advertisement = car_webpage.find_all('div', class_='mod-b-card__footer')
    return car_advertisement


def get_car_attribute(item: BeautifulSoup) -> dict:
    """
    Extract car details such as car name, mileage, transmission, location, price and monthly instalment.

    Args:
        item BeautifulSoup: Contain car advertisement details.

    Returns:
        dict: Return car attribute details.
    """
    try:
        car_dict = {}
        car_name = item.find('a', 'mod-b-card__title').get_text(strip=True).split()
        car_name_joined = ' '.join(car_name)
        car_dict['car_name'] = car_name_joined
        car_mileage = item.find('div', 'mod-b-card__car-other')

        if car_mileage:
            spans = car_mileage.find_all('span')
            car_dict['car_mileage'] = spans[0].get_text(strip=True) if len(spans) > 0 else 'None'
            car_dict['car_transmission'] = spans[1].get_text(strip=True) if len(spans) > 1 else 'None'
            car_dict['car_location'] = spans[2].get_text(strip=True) if len(spans) > 2 else 'None'

        car_dict['car_price'] = item.find('div', 'mod-card__price__total').get_text(strip=True)
        car_dict['car_monthly_instalment'] = item.find('div', 'mod-tooltipMonthPay').get_text(strip=True)
        logging.info(f"Appended: {car_dict}")
    except Exception as e:
        logging.error(f"Error in function get_car_attribute: {e}")
        sys.exit(1) # Program will stop immediately if there is any error

    return car_dict


def save_list_to_csv(list_of_car: list[dict], filename: str) -> None:
    """
    Save the extracted details into a csv file.

    Args:
        list_of_car list[dict]: Contain all extracted car data.
        filename str: The filename of output file.

    Returns:
        None: This function only to create csv file and write data in it.
    """
    fieldnames = list(list_of_car[0].keys())
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for row in list_of_car:
            writer.writerow(row)

    logging.info(f"Data has been inserted into file {filename}")


def get_date_timestamp() -> str:
    """
    Create timestamp in YYYYMMDDHHMMSS format.

    Returns:
        str: Return current timestamp.
    """
    now = datetime.datetime.now()
    timestamp_str = now.strftime("%Y%m%d%H%M%S")
    return timestamp_str


def main():
    try:
        current_timestamp = get_date_timestamp()
        filename = f"car_{current_timestamp}.csv"
        car_attributes = []

        car_data = get_html()
        if car_data is None:
            logging.error("Failed to retrieve initial data")
            return # Program will stop if initial webpage is empty

        page_number_list = get_page_number_list(car_data)
        max_page_number = get_max_page_number(page_number_list)
        for i in range(1 , max_page_number + 1):
            car_data_by_webpage = get_html(i)
            if car_data_by_webpage is None:
                logging.error(f"Failed to retrieve data for webpage {i}")
                continue # Program will continue to iterate next page if current webpage is None
            else:
                car_data_html = get_car_list(car_data_by_webpage)
                for car in car_data_html:
                    car_attributes.append(get_car_attribute(car)) # Append dictionary that contain car attributes into a list
                logging.info(f"Completed scraping in page {i}")
                time.sleep(5)

        if car_attributes:
            save_list_to_csv(car_attributes, filename)
        else:
            logging.error("No car data collected")
    except Exception as e:
        logging.error(f"{e}")



if __name__ == '__main__':
    main()
