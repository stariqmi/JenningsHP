import xlwt

# Create XLS sheet
workbook = xlwt.Workbook()
worksheet = workbook.add_sheet("details")

# Open results.csv
csv = open("results.csv")
lines = csv.readlines()

# Write lines from csv to XLS
for r in range(0,len(lines)):
	print lines[r]
	row = lines[r].decode("utf-8").split(',')
	for c in range(0,len(row)):
		worksheet.write(r,c,row[c])

# Save Workbook
workbook.save("results.xls")