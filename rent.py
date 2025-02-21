from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import csv
import time
import os
import re
import smtplib
from email.mime.text import MIMEText
import config

def wait_and_find_element(driver, by, value, timeout=20):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except TimeoutException:
        print(f"Timeout waiting for element: {value}")
        return None

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--start-maximized')
    options.add_argument(f"--user-data-dir=C:\\Users\\{os.getenv('USERNAME')}\\AppData\\Local\\Google\\Chrome\\User Data")
    options.add_argument('--profile-directory=Default')
    try:
        service = Service('chromedriver.exe')
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        print(f"Error setting up driver: {str(e)}")
        raise

def load_existing_listings(filename):
    """ Load existing listings from CSV to avoid duplicates """
    existing_urls = set()
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                url = row["url"]
                cleaned_url = url.split("?")[0].strip()
                existing_urls.add(cleaned_url)
    return existing_urls

def extract_price(title):
    """ Extracts the price from the title and converts it to an integer """
    price_match = None
    # Try UYU format
    uyumatch = re.search(r'UYU\s?([\d,]+)', title)
    if uyumatch:
        price_match = uyumatch
    # Try dollar format
    if not price_match:
        usdmatch = re.search(r'\$(\d,*)', title)
        if usdmatch:
            price_match = usdmatch
    if price_match:
        price = int(price_match.group(1).replace(',', ''))
        return price
    return None

def send_email(subject, body, sender, recipients, password):
    """ Send email notification using Gmail SMTP """
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = ', '.join(recipients)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(sender, password)
            smtp_server.sendmail(sender, recipients, msg.as_string())
        print("Email sent successfully!")
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def scrape_marketplace():
    driver = None
    csv_filename = 'rentals_listings.csv'  
    
    # Email configuration
    EMAIL_SENDER = config.sender
    EMAIL_PASSWORD = config.password
    EMAIL_RECIPIENTS = config.recipient
    
    try:
        driver = setup_driver()
        
        # Dictionary to store listings from both queries
        all_listings = []
        
        # Search queries
        search_queries = [
            "alquiler por deposito",
            "alquiler por luc"
        ]
        
        for query in search_queries:
            driver.get(f"https://www.facebook.com/marketplace/category/search?query={query}")
            print(f"Navigated to Facebook Marketplace with search query: {query}")
            time.sleep(5)
            
            existing_urls = load_existing_listings(csv_filename)
            new_listings = []
            items = driver.find_elements(By.CSS_SELECTOR, "a[role='link']")
            print(f"Found {len(items)} items for query: {query}")
            count = 0
            
            for item in items:
                try:
                    if count >= 20:
                        break
                    href = item.get_attribute("href")
                    if not href or "marketplace/item" not in href:
                        continue
                    cleaned_href = href.split("?")[0].strip()
                    if cleaned_href in existing_urls:
                        continue
                    
                    title_element = item.find_element(By.CSS_SELECTOR, "span[class]")
                    title = title_element.text.strip()
                    price = extract_price(title)
                    
                    # Keep the same price filtering logic
                    if price is None:
                        print(f"Skipping {title} (No valid price found)")
                        continue
                    if price > 19000:
                        print(f"Skipping {title} (Price: UYU{price})")
                        continue
                    if price < 14000:
                        print(f"Skipping {title} (Price: UYU{price})")
                        continue
                    
                    if title and href:
                        new_listings.append({
                            "title": title,
                            "url": href
                        })
                    print(f"New valid listing found: {title} (Price: UYU{price})")
                    count += 1
                
                except Exception as e:
                    print(f"Error processing item: {str(e)}")
                    continue
            
            all_listings.extend(new_listings)
        
        if all_listings:
            file_exists = os.path.exists(csv_filename)
            with open(csv_filename, 'a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=["title", "url"])
                if not file_exists:
                    writer.writeheader()
                writer.writerows(all_listings)
            
            # Send email notification
            subject = f"New Rental Listings Found on Facebook Marketplace ({len(all_listings)})!"
            body = "\n".join([f"{listing['title']} - {listing['url']}" for listing in all_listings])
            send_email(subject, body, EMAIL_SENDER, EMAIL_RECIPIENTS, EMAIL_PASSWORD)
            print(f"Added {len(all_listings)} new valid listings to {csv_filename}")
        else:
            print("No new valid listings found")
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        if driver:
            driver.quit()

def main():
    """Main function to run the continuous monitoring loop"""
    print("Starting continuous marketplace monitoring...")
    print("Press Ctrl+C to stop the script")
    try:
        while True:
            print("\nChecking for new listings...")
            scrape_marketplace()
            print(f"Sleeping for 120 minutes...")
            time.sleep(7200)  # 7200 seconds = 2 hours
    except KeyboardInterrupt:
        print("\nScript stopped by user")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        print("Cleaning up...")
        if 'driver' in locals() and driver is not None:
            driver.quit()

if __name__ == "__main__":
    main()