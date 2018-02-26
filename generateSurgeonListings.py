# This script will build a listing of all procedures that a surgeon can book
# Input files should be encoded as UTF-8
# Author: Aaron Suggitt
# Future Enhancements:
#    - Compare previously generated file to new output. Only export if changes occurred
#    - Add header to each output page
#    - Better position Report generated label (right justify)
#    - Column wrapping for long procedures
#    - Add different options for output (DPC List, SOA List)

import csv

from operator import itemgetter
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import BaseDocTemplate, SimpleDocTemplate, Frame, Table, TableStyle, Paragraph, Spacer, PageTemplate, NextPageTemplate, PageBreak, PageTemplate
from reportlab.rl_config import defaultPageSize
from functools import partial
from datetime import datetime

PAGE_HEIGHT = defaultPageSize[1]
PAGE_WIDTH = defaultPageSize[0]
styles = getSampleStyleSheet()
normalStyle = styles['Normal']


def header(canvas, doc, content):
    canvas.saveState()
    w, h = content.wrap(doc.width, doc.topMargin)
    canvas.setFont('Helvetica-Bold', 18)
    canvas.drawCentredString(doc.width/2+75, doc.height + doc.topMargin - h, content.text)
    canvas.restoreState()

def addProcedureHint(code, procedure, procedure_hints_list):
    # Search hints list for procedure
    for hint in procedure_hints_list:
        if hint[0] == code:
            procedure = procedure + "\n    " + hint[2]
            break
    return procedure

# Open and read hints file
with open('source/procedure_hints.csv', 'r') as procedureHintsFile:
     procedure_hints_list = list(csv.reader(procedureHintsFile, delimiter=',', quotechar='"'))
     procedure_hints_list.pop(0)
procedureHintsFile.close

# Open and read DPC procedures file
with open('source/dpc_cards.csv', 'r') as dpcCardFile:
     dpc_list = list(csv.reader(dpcCardFile, delimiter=',', quotechar='"'))
     dpc_list.pop(0)
dpcCardFile.close

# Open and read DPC SRPG file
with open('source/srpg_cards.csv', 'r') as srpg_card_file:
     srpg_list = list(csv.reader(srpg_card_file, delimiter=',', quotechar='"'))
     srpg_list.pop(0)
srpg_card_file.close

# Open and read surgeon file
with open('source/surgeons.csv', 'r') as surgeonFile:
     surgeonList = list(csv.reader(surgeonFile, delimiter=',', quotechar='"'))
     surgeonList.pop(0)
surgeonFile.close

# Open and read SRPG procedures file
with open('source/srpg_procedures.csv', 'r') as srpg_procedures_file:
     srpg_procedures_list = list(csv.reader(srpg_procedures_file, delimiter=',', quotechar='"'))
     srpg_procedures_list.pop(0)
srpg_procedures_file.close

# Begin creation of unique surgeons list
current_surgeon = surgeonList[0][0],surgeonList[0][1],surgeonList[0][2],surgeonList[0][3]
uniqueSurgeons = []
uniqueSurgeons.append(current_surgeon)
best_practice_dict = {}

i = 0
for row in surgeonList:
    current_surgeon = surgeonList[i][0],surgeonList[i][1],surgeonList[i][2],surgeonList[i][3]
    
    # Check if surgeon is BEST PRACTICE. If so add to dictionary
    if (current_surgeon[1] == 'BEST PRACTICE'):
        best_practice_dict[current_surgeon[0]] = current_surgeon[2]

    # Search uniqueSurgeons for current_surgeon. If not found add, otherwise skip
    new_surgeon = "true"
    for rowUnique in uniqueSurgeons:
        if (current_surgeon[0] in rowUnique):
            new_surgeon = "false"
            break
    if (new_surgeon == "true"):
        uniqueSurgeons.append(current_surgeon)
    i = i+1

i = 0
surgeon_dpc_list = []

for surgeon in uniqueSurgeons:

    # ====== Find all surgeon specific DPCs ============
    for dpc in dpc_list:
        if(surgeon[0] == dpc[3]):
            dpc[6] = str(addProcedureHint(dpc[5], dpc[6], procedure_hints_list))
            surgeon_dpc_list.append(dpc)
       
    # ====== Find all best practice service DPCs =======
    for dpc in dpc_list:
        #check if current card is best practice
        if(dpc[3] in best_practice_dict):
            #Get best practice card service from surgeon name
            best_practice_service = dpc[4].split(',')
            best_practice_service.pop(0)
            best_practice_service = ''.join(best_practice_service)
            best_practice_service = best_practice_service.strip()

            #Check if the best practice service matches our current surgeon service
            if (best_practice_service == surgeon[3]):
                #Check if procedure already exists in surgeon_dpc_list
                procedure_found = 'false'
                for key_card in surgeon_dpc_list:
                    if (dpc[5] == key_card[5]):
                        procedure_found = 'true'
                if (procedure_found == 'false'):     
                    surgeon_dpc_list.append(dpc)
    
    # ====== Find all surgeon specific SRPGs =======
    for srpg_card in srpg_list:
        if(surgeon[0] == srpg_card[3]):
            #SRPG found. Get procedures for SRPG and add to list
            for srpg in srpg_procedures_list:
                #check if srpg description matchs srpg card description
                if (srpg_card[6] == srpg[1]):
                    
                    #check if sprg card for procedure already exists in dpc list. If not, add
                    procedure_found = 'false'
                    for key_card in surgeon_dpc_list:
                        if (srpg[2] == key_card[5]):
                            procedure_found = 'true'
                    if (procedure_found == 'false'):
                        temp = list(srpg_card)        
                        #overwrite SRPG code with procedure code
                        temp[5] = srpg[2]
                        #overwrite SRPG description with procedure description
                        temp[6] = srpg[3]
                        surgeon_dpc_list.append(temp)
                                        
    # ====== Find all best practice specific SRPGs =======
    for srpg_card in srpg_list:
        #check if current card is best practice
        if(srpg_card[3] in best_practice_dict):
            #Get best practice card service from surgeon name
            best_practice_service = srpg_card[4].split(',')
            best_practice_service.pop(0)
            best_practice_service = ''.join(best_practice_service)
            best_practice_service = best_practice_service.strip()
              
            #Check if the best practice service matches our current surgeon service
            if (best_practice_service == surgeon[3]):
                #Check if procedure already exists in surgeon_dpc_list
                 for srpg in srpg_procedures_list:
                    #check if srpg description matches srpg card description
                    if (srpg_card[6] == srpg[1]):
                        #check if sprg card for procedure already exists in dpc list. If not, add
                        procedure_found = 'false'
                        for key_card in surgeon_dpc_list:
                            if (srpg[2] == key_card[5]):
                                procedure_found = 'true'
                        if (procedure_found == 'false'):
                            temp = list(srpg_card)        
                            #overwrite SRPG code with procedure code
                            temp[5] = srpg[2]
                            #overwrite SRPG description with procedure description
                            temp[6] = srpg[3]
                            surgeon_dpc_list.append(temp)           
    
    #Setup variables for PDF output
    output_path = 'surgeon_listings/' + surgeon[1] + '_' + surgeon[2] + '.pdf'
    elements = []
    
    #sort surgeon_dpc_list by procedure definition
    if surgeon_dpc_list:
        dpc_table = []
        for card in surgeon_dpc_list:
            dpc_table.append([card[5],card[6],str(card[1])])
        dpc_table = sorted(dpc_table,key=itemgetter(1))
        dpc_table.insert(0,["CODE","DESCRIPTION for " + surgeon[1],"DPC"])
        t=Table(dpc_table, repeatRows=1, splitByRow='true')
        t.setStyle(TableStyle([
                        ('GRID',(0,0), (-1,-1), 0.25, colors.black),
                        ('ALIGN',(0,0), (0,-1), 'CENTER'),
                        ('VALIGN',(0,0), (0,-1), 'MIDDLE'),
                        ('ALIGN',(2,0), (2,-1), 'CENTER'),
                        ('VALIGN',(2,0), (2,-1), 'MIDDLE'),
                        ('BACKGROUND',(0,0), (2,0),colors.black),
                        ('TEXTCOLOR',(0,0), (2,0),colors.white)]))
        
        doc = SimpleDocTemplate(output_path,
                                rightMargin=70,
                                leftMargin=70,
                                topMargin=20,
                                bottomMargin=42)
        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height-2*cm, id='normal')
        surgeon_name = Paragraph((surgeon[1] + ', ' + surgeon[2] + " - " + surgeon[3]), normalStyle)
        template = PageTemplate(id='header', frames=[frame], onPage=partial(header, content=surgeon_name))
        doc.addPageTemplates([template])
        
        Story = [Spacer(0,0*inch)]
        Story.append(NextPageTemplate('header'))
        Story.append(t)
        
        # Get current datetime for printing on report
        generated = str(datetime.now())
        generated = generated[:10]
        report_generated = Paragraph(("Report generated: " + generated), normalStyle)
        Story.append(report_generated)
        doc.build(Story)

    i = i + 1
    #clean dpc list for next surgeon
    surgeon_dpc_list = []
