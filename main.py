from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from WebDriverManager import WebDriverManager
from DatasSelectionService import DataSelectionService
from datetime import datetime
import time
import sys

END_DATE = datetime(2025, 5,1)
XPATHS={
    'ButtonCentralMarginal':'//*[@id="dnn_ctr953_ModuleContent"]/div/ul/li[2]',
    'CheckBox':'//div[contains(text(), "Ponderada")]',
    'Button_yesterday':'/html/body/form/div[4]/div/section[2]/div[4]/div/div/div[1]/div[2]/div/div/div/div[2]/div/div/div/div/div[2]/div/div[1]/div[1]/div/div/div[1]/div[2]/div/i',
    'Table':'/html/body/form/div[4]/div/section[2]/div[4]/div/div/div[1]/div[2]/div/div/div/div[2]/div/div/div/div/div[2]/div/div[2]/div/div[6]/div/table'

}

def check_date_validate():
    now = datetime.now()
    if now > END_DATE:
        print("No se puede continuar. Error")
        time.sleep(5)
        sys.exit()  # Cierra el programa

def init_workflow():
    # Verificar la fecha antes de ejecutar el script
    check_date_validate()

    browser = 'chrome'
    web = WebDriverManager(browser=browser, headless=False)
    web_driver = web.init_driver()

    print('Cargando Pagina web....')
    web_driver.get('https://www.oc.do/Servicios/Reporte/CostosMarginales')
    wait = WebDriverWait(web_driver, 30)
    


    # Hacer clic en el botón Central Marginal
    print('Click en el boton Central Marginal')
    ButtonCentralMarginal = wait.until(EC.element_to_be_clickable((By.XPATH, XPATHS.get('ButtonCentralMarginal'))))
    ButtonCentralMarginal.click()
    

    
    # Hacer clic en el checkbox "Ponderada"
    print('Haciendo Click en Ponderada')
    CheckBox = wait.until(EC.element_to_be_clickable((By.XPATH, XPATHS.get('CheckBox'))))
    CheckBox.click()

    # Hacer clic en el botón de ayer
    print('Haciendo Click en Ayer')
    Button_yesterday=wait.until(EC.element_to_be_clickable((By.XPATH, XPATHS.get('Button_yesterday'))))
    Button_yesterday.click()

    now = datetime.now()
    DataSelect = DataSelectionService(None, None, None, 10, int(now.day)-1, now.month, now.year, typology_key='Dominicana')
    time.sleep(5)
    print('Obteniendo datos')
    DataSelect._extract_table(
        wait, '', XPATHS.get('Table')
    )


init_workflow()