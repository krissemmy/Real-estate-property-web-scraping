import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import datetime
from sqlalchemy import create_engine


# Define the path to the ChromeDriver executable
serve = Service("/home/krissemmy/anaconda3/chromedriver_linux64/chromedriver.exe")
option = Options()

#add option to disable website notifications
option.add_experimental_option("prefs", {"profile.default_content_setting_values.notifications": 2 }) 

driver = webdriver.Chrome(service = serve, options = option)
website = 'https://nigeriapropertycentre.com/'
driver.get(website)
driver.maximize_window()
time.sleep(1)

#filter for property only for rent
pro_type = driver.find_element(By.XPATH,'//*[@id="divHeaderWrapper"]/header/div/div/div[2]/ul/li[3]/a')
pro_type.click()

#filter for property only in Lagos
filter = driver.find_element(By.XPATH, '//*[@id="rmjs-1"]/li[25]/a')
time.sleep(1)
filter.click()

#get the number of pages existing
length = driver.find_element(By.XPATH, '/html/body/div[1]/section/div/div/div/div[1]/div[5]/ul/li[14]/a')
length = int(length.text)


for k in range(length):
    with open('p.csv','a',newline='') as file: 
        for i in range(1,24):
            time.sleep(2)
            try:
                title = driver.find_element(By.XPATH, f'//div[{i}]/div/div/div[3]/div[3]/a/h4')
                time.sleep(0.2)

                date_added = driver.find_element(By.XPATH, f'//div[{i}]/div/div/div[3]/div[3]/div/span')
                time.sleep(0.2)

                price = driver.find_element(By.XPATH, f'//div[{i}]/div/div/div[3]/div[3]/span[1]/span[2]')
                time.sleep(0.2)
                
                pay_by = driver.find_element(By.XPATH, f'//div[{i}]/div/div/div[3]/div[3]/span[1]/span[3]')
                time.sleep(0.2)
                
                try:
                    company_agent = driver.find_element(By.XPATH, f'//div[{i}]/div/div/div[3]/div[3]/span[3]')
                    company_agent = company_agent.text.split('\n')
                    company_agent = ' '.join(company_agent)
                except:
                    pass
                time.sleep(0.2)

                location = driver.find_element(By.XPATH, f'//div[{i}]/div/div/div[3]/div[3]/address/strong')
                time.sleep(0.2)
                
                try:
                    listing = driver.find_element(By.XPATH, f'//div[{i}]/div/div/div[1]/span')
                except:
                    pass
                time.sleep(0.2)

            except:
                pass
        
            file.write(f"{title.text} | {date_added.text} | {company_agent}\
            | {location.text} | {listing.text} | {price.text} | {pay_by.text}\n")
            time.sleep(1)
    next_page = driver.find_element(By.LINK_TEXT,'›')
    next_page.click()
    time.sleep(2)
    
    
col = ['title', 'date_added', 'company_agent', 'location', 'listing','price', 'payment_plan']

df = pd.read_csv("property.csv", delimiter='|', names=col)

#drop all duplicate entries in the dataframe
df.drop_duplicates(inplace=True)

#reset the index of the dataframe
df.reset_index(inplace=True)

#delete the old index in the dataframe
df.drop('index', axis=1, inplace=True)
    
    
def rem_empty_space(x):
    '''
    Remove leading and trailing empty space
        Parameter:
            x(object): a string of character
        Returns:
            x: the string without the any leding empty space and trailing empty space'''
    x = str(x)
    return x.strip()

#a loop to apply the rem_empty_space function on all columns
for i in col:
    df[i] = df[i].apply(rem_empty_space)


def get_contact(x):
    '''
    Get the contact number of the company/agent renting the property out,
    from the company/agent column
        Parameter:
            x(object): a string of characters
        Returns:
            x[-1]: the last element in the list which is the phone number of the company/agent
    '''
    x = x.split(' ')
    return x[-1]

df['contact_no'] = df['company_agent'].apply(get_contact)

def get_com_agt(x):
    '''
    Get only the company/agent name to be stored in the column,
    by splitting the string into a list of substring and then join the substring
    representing the company/agent name
        Parameter:
            x(object): a string of character
        Returns:
            x: a string of company/agent name  
    '''
    x = x.split(' ')
    x = ' '.join(x[:-1])
    return x

df['company_agent'] = df['company_agent'].apply(get_com_agt)

def clean_con_no(x):
    '''
    Clean the contact_no column snd make all records to be in one format,
    and make NaN those that are incorrect or empty 
        Parameter:
            x(object): a string of character
        Returns:
            x: 0 added to the beginning of the number(x) to make it a complete phone number 
    '''
    x = str(x)
    if '+' in x:
        x = x[4:]
        return '0'+ x
    elif x.startswith('234-'):
        x = x[4:]
        return '0'+ x
    elif x.startswith('2'):
        x = x[3:]
        return '0'+ x
    elif len(x) < 11:
        return pd.NA
    else:
        return x
    
    
df['contact_no'] = df['contact_no'].apply(clean_con_no)

def del_wrong_no(x):
    '''
    Change any phone number that is not 11 characters long to NAN 
        Parameter:
            x(object): a string of character
        Returns:
            x: pd.NA if x is longer than 11, or else it will return the phone number 
    '''
    x = str(x)
    if len(x) > 11:
        return pd.NA
    else:
        return x
    
df['contact_no'] = df['contact_no'].apply(del_wrong_no)

def get_date(x):
    '''
    Get the current date, yesterday's date and every entries day in numeric format
        Parameter:
            x(object): a string of character
        Returns:
            x: the date in numeric d/m/y format 
    '''
    x = str(x)
    if 'Today' in x:
        return datetime.datetime.today().strftime ('%d/%m/%Y')
    elif 'Yesterday' in x:
        previous_date = datetime.datetime.today() - datetime.timedelta(days=1)
        return previous_date.strftime ('%d/%m/%Y')
    elif x.startswith('Added'):
        x = x.split(' ')
        x = x[2:]
        x = ' '.join(x)
        x = datetime.datetime.strptime(x, '%d %b %Y')
        x = x.strftime('%d/%m/%Y')
        return x
    else:
        return x
    
df['date_added'] = df['date_added'].apply(get_date)

def get_list(x):
    '''
    Get the listing of the property
        Parameter:
            x(object): a string of character
        Returns:
            x: the listing without the "listing" word in it or else return NaN
    '''
    if len(x) > 0:
        x = str(x)
        x = x.split(' ')
        x = ' '.join(x[:-1])
        return x
    else:
        return pd.NA
    
df['listing'] = df['listing'].apply(get_list)

def change_price(x):
    '''
    Remove the comma's in the price/amount using the .split() and .join() method
        Parameter:
            x(object): a string of character
        Returns:
            x: the number joined together without th commas 
    '''
    x = str(x)
    x = x.split(',')
    x = ''.join(x)
    return x

df['price'] = df['price'].apply(change_price)

#change the dtype to integer
df['price'] = df['price'].astype('Int64')

#Accepts user inputs for the database connection 
user = input("input your database username: ")
db_name = input("input your database name: ")
password = input("input your database password: ")
host = input("input your connection url/hostname: ")
port = input("input your connection port: ")

#create an engine variable to initiate connection to the postgres database
engine = create_engine(f'postgresql://{user}:{str(password)}@{str(host)}:{str(port)}/{str(db_name)}')

#load the dataframe into the database
df.to_sql('property',engine,index=False, if_exists='replace')

print("table property imported to database completed")