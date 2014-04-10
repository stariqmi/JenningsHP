import pprint, os, requests, glob
from bs4 import BeautifulSoup
from selenium import webdriver

# Helper function that takes in lines from the details.txt
# And locates the name and address
def find_address(lines):
	# Find position of address
	addr_pos = 0
	for line in lines:
		if "name and address of taxpayer" in line.lower():
			addr_pos += 1
			break
		else:
			addr_pos += 1

	# Get details from address
	addr_lines = []
	for line in lines[addr_pos:]:
		if line != "\n":
			addr_lines.append(line)
		else:
			break

	return {
		"name": addr_lines[0].strip(),
		"street_address": addr_lines[1].strip(),
		"city": addr_lines[-1].split("    ")[0].strip(),
		"zip": addr_lines[-1].split("    ")[-1].strip().split("-")[0]
	}


# Helper function that takes in lines from the details.txt
# And locates the tax amounts for fall and spring
def find_taxes(lines):
	positions = []
	pos = 0
	for line in lines:
		if "MAKE CHECK PAYABLE TO" in line.upper():
			positions.append(pos)
		pos += 1

	# Spring Tax
	for line in lines[positions[0]:]:
		if "$" in line:
			spring_tax = line.split("$")[1].strip()
			break

	# Fall Tax
	for line in lines[positions[1]:]:
		if "$" in line:
			fall_tax = line.split("$")[1].strip()
			break
			
	return [spring_tax,fall_tax]


# Find owner name, mainling address and tax owed via HTTP request to
# https://www.invoicecloud.com/portal/(S(jbmooiiaiujo4jfohejebbmd))/customerlocator.aspx?iti=8&bg=3a912998-0175-4640-a401-47fabc0fc06b&vsii=1
# @params parcel_no, string representing the parcel number to search for
# @params driver, webdriver
def find_details(parcel_no, driver):
	# Acces main search page and execute search by parcel number
	driver.get('https://www.invoicecloud.com/portal/(S(jbmooiiaiujo4jfohejebbmd))/customerlocator.aspx?iti=8&bg=3a912998-0175-4640-a401-47fabc0fc06b&vsii=1')
	parcel_field = driver.find_element_by_id('rptInputs_ctl01_txtValue')
	parcel_field.send_keys(parcel_no)	# Enter parcel number into appropriate field
	driver.find_element_by_id('btnSearch').click()	# Submit the form

	# Parse the result for the relevant PDF links
	search_html = BeautifulSoup(driver.page_source.encode('utf-8',''))
	pdf_links = []
	links = search_html.find_all('a')
	for link in links:
		if 'pdfviewer' in link.get('href',''):
			pdf_links.append(link['href'])
	if len(pdf_links) > 0:
		# Save pdf
		req = requests.get(pdf_links[0])
		pdf = open('details.pdf','wb')
		pdf.write(req.content)
		pdf.close()

		# Call cmd shell to convert pdf to text
		# Replace 0 with 'parcel_no' in the following 2 lines to have different PDFs texts for each parcel number  
		os.system('pdf2txt.py details.pdf > details_{0}.txt'.format(parcel_no))
		details_txt = open("details_{0}.txt".format(parcel_no))
		lines = details_txt.readlines()
		details = find_address(lines)
		taxes = find_taxes(lines)
		details["spring_tax"] = taxes[0].replace(',','')
		details["fall_tax"] = taxes[1].replace(',','')
		return details
		

	else:
		print "No results for parcel number ------ {0}".format(parcel_no)
		return False


# Parses Text File to create a tab delimeted array from each line
def parse_text():
	driver = webdriver.PhantomJS()
	results_txt = open("results.csv", "w")	# Open for writing
	failed_txt = open("failed.txt", "w")	# Open for writing

	# Open tax.txt
	tax_text = open("tax.txt")	# Open for reading
	tax_lines = tax_text.readlines()
	headers = tax_lines[0].split('\t')
	results_txt.write(','.join(["spr_tax","fall_tax"] + headers[:2] + ["first_name","last_name"] + headers[3:]))
	
	# For each line in tax.txt
	for line in tax_lines:
		data = line.split('\t')
		print "Searching for parcel number ------ {0}".format(data[0])
		try:
			details = find_details(data[0],driver)
			if details:
				# Update data with details
				data[2] = details["name"].split(',')[0]
				data[3] = details["name"].split(',')[1] if len(details["name"].split(',')) > 1 else ""
				data[4] = details["street_address"].replace(',','')
				data[5] = details["city"].replace(',','-')
				data[6] = details["zip"]
				result = [details["spring_tax"],details["fall_tax"]] + data
				
				print ",".join(result)
				results_txt.write(",".join(result))
		except Exception as exc:
			print "ERROR:\n{0}".format(exc)
			print "Search failed for parcel number ------ {0}".format(data[0])	
			failed_txt.write('\t'.join(data))

	failed_txt.close()
	results_txt.close()

# Parse failed text
def parse_failed():
	driver = webdriver.PhantomJS()
	results_txt = open("results.csv", "a")	# Open for appending

	
	# Transfer failed results from  
	failed_txt = open("failed.txt")	# Open for reading
	tax_lines = failed_txt.readlines()
	failed_txt.close()	# Close

	failed_txt = open("failed.txt","w")	# Open for writing

	# For each line in tax.txt
	for line in tax_lines:
		data = line.split('\t')
		print "Searching for parcel number ------ {0}".format(data[0])
		try:
			details = find_details(data[0],driver)
			if details:
				# Update data with details
				data[2] = details["name"].split(',')[0]
				data[3] = details["name"].split(',')[1]
				data[4] = details["street_address"].replace(',','')
				data[5] = details["city"].replace(',','-')
				data[6] = details["zip"]
				result = [details["spring_tax"],details["fall_tax"]] + data
				
				print ",".join(result)
				results_txt.write(",".join(result))
		except Exception as exc:
			print "ERROR:\n{0}".format(exc)
			print "Search failed for parcel number ------ {0}".format(data[0])	
			failed_txt.write('\t'.join(data))

	failed_txt.close()
	results_txt.close()