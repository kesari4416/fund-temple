from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from.serializers import PeopleInterestDetailsSerializer
from .models import PeopleInterestDetails
from token_app.views import *
from management.models import ManagementDetails
import datetime
from collection.models import CollectionDetails
from collection.serializers import CollectionDetailsSerializer

from balancesheet.models import PeopleInterestBalanceSheet
from balancesheet.serializers import PeopleInterestBalanceSheetSerializer
# calculate sum
from django.db.models import Sum
from permisions.models import Permisions
from family.models import Fammily_Details,Member_Details
from family.serializers import Fammily_DetailsSerializer,member_DetailsSerializer
from treasure.models import ManagementTreasure
from chit_fund.models import ChitFundInvesters,ChitFundsDetails
from reports.models import Report,TempleMemberReport,FundMemberReport,ChitFundInterestOverallReport,InterestPeopleReport
from reports.serializers import InterestPeopleReportserializer
from reports.models import ChitFundInterestOverallReport
from reports.serializers import ChitFundInterestOverallReport_serializer
from dateutil.relativedelta import *
from balancesheet.serializers import *





@api_view(['GET','POST'])
def add_interest_given_details(request):
    rejin=token_checking(request)
    if not rejin:
        return Response({"message":"No User Found"},status=status.HTTP_401_UNAUTHORIZED)
    if not rejin.is_active:
        return Response({"message":"Not Authorized Please Contact Admin"},status=status.HTTP_401_UNAUTHORIZED)
    get_role=rejin.user_role
    if rejin.my_role!=None:
        permiss=Permisions.objects.filter(role_link_id=rejin.my_role.id).first()
        if permiss:
            perm=Permisions.objects.get(role_link_id=rejin.my_role.id)   
    check_management=ManagementDetails.objects.all()
    if not check_management:
        dict6={}
        dict6['message']= "First Add Management Profile details"
        return Response(dict6,status=status.HTTP_406_NOT_ACCEPTABLE)
    else: 
        management=ManagementDetails.objects.all().first()
    if request.method =='POST':  
        if get_role=="User" and perm.interest_add ==True or get_role=="Admin" or rejin.is_superuser == True:    
            serializer876 = PeopleInterestDetailsSerializer(data=request.data)
            interest_type= request.data['interest_type']
            interest_date=request.data['interest_date']
            interest_category=request.data['interest_category']
            date_object = datetime.datetime.strptime(interest_date, "%Y-%m-%d")
            if interest_category == "Installment Interest" and date_object.month!=datetime.datetime.now().month:
                msg={'msg':'Installment interest cannot be added for previous month'}
                return Response(msg,status=status.HTTP_226_IM_USED)
            if serializer876.is_valid():
                interest_type= request.data['interest_type']
                # if request.data['interest_category'] == "Installment Interest":
                #     bal_new1=request.data['final_amt_given']
                # else:
                #     bal_new1=request.data['principal_amt']
                if interest_type=="Management Interest":
                    managefil=ManagementTreasure.objects.filter(management_profile=management)
                    if managefil:
                        manage=ManagementTreasure.objects.get(management_profile=management)
                        if (float(manage.cash_in_hand)-float(manage.expence_amt)) < float(request.data['principal_amt']):
                            msg={'msg':'Insufficient amount in cash in hand'}
                            return Response(msg,status=status.HTTP_226_IM_USED)
                elif interest_type=="Chit fund Interest":
                    chit_fund_obj= ChitFundsDetails.objects.filter(id=request.data['chitt_fund'])
                    if chit_fund_obj:
                        chit_fund_get=ChitFundsDetails.objects.get(id=request.data['chitt_fund'])
                     
                        if float(chit_fund_get.cash_inhand_amount) < float(request.data['principal_amt']):
                            msg={'msg':'Insufficient amount in chit fund'}
                            return Response(msg,status=status.HTTP_226_IM_USED)
                temp_family=serializer876.save()
                temp_family.created_by=rejin.id
                temp_family.management_profile=management
                temp_family.save()
                if interest_type=="Management Interest":
                    managefilter=ManagementTreasure.objects.filter(management_profile=management)
                    if managefilter:
                        manage_get=ManagementTreasure.objects.get(management_profile=management)
                        # manage_get.cash_in_hand = float(manage_get.cash_in_hand) - float(temp_family.principal_amt)
                        manage_get.expence_amt = float(manage_get.expence_amt) + float(temp_family.principal_amt)
                        manage_get.save()

                    pppp=Report.objects.create(interest=temp_family,management_profile=management,created_by =rejin.id,type_choice='Reduction',amount=temp_family.principal_amt,members=temp_family.people_member)
                    pppp.created_at=temp_family.interest_date
                    pppp.save()
                    if temp_family.apply_first_interest == True:
                        pay1=float(temp_family.interest_amt)
                        pppp=Report.objects.create(interest=temp_family,management_profile=management,created_by =rejin.id,type_choice='Addition',amount=pay1,members=temp_family.people_member)
                        pppp.created_at=temp_family.interest_date
                        pppp.save()
                    
                   
                elif interest_type=="Chit fund Interest":
                    chit_fund_object= ChitFundsDetails.objects.filter(id=temp_family.chitt_fund.id)
                    if chit_fund_object:
                        chit_fund_get_new=ChitFundsDetails.objects.get(id=temp_family.chitt_fund.id)
                        chit_fund_get_new.cash_inhand_amount=float(chit_fund_get_new.cash_inhand_amount) - float(request.data['principal_amt'])
                        chit_fund_get_new.principal_given_amount=float(chit_fund_get_new.principal_given_amount) + float(request.data['principal_amt'])
                        chit_fund_get_new.save()
                        sssss=ChitFundInterestOverallReport.objects.create(interest=temp_family,chitfund=temp_family.chitt_fund,amount=float(request.data['principal_amt']),management_profile=management,income_choice='Principal Given',created_by=rejin.id)
                        sssss.created_at=temp_family.interest_date
                        sssss.save()
                        if temp_family.apply_first_interest ==True:
                            pppp=ChitFundInterestOverallReport.objects.create(created_at=temp_family.interest_date,chitfund=temp_family.chitt_fund,management_profile=management,created_by=rejin.id,amount=temp_family.interest_amt,interest=temp_family,income_choice="Addition")
                            pppp.created_at=temp_family.interest_date
                            pppp.save()
                            

                
                # if temp_family.apply_first_interest ==True:
                #     if temp_family.interest_category == "Installment Interest":
                #         pay=float(temp_family.interest_amt)
                #     else:
                #         pay=0
                # else:
                pay = 0 
                if temp_family.interest_category == "Installment Interest":
                    bal=float(temp_family.final_amt_given)-pay
                else:
                    bal=float(temp_family.principal_amt)-pay   
                    
                # bal_sheet=PeopleInterestBalanceSheet.objects.create(management_profile=management,interest=temp_family,principal_balance=bal,
                #             principal_amt=temp_family.principal_amt,credit_amt=bal,debit_amt=pay,balance_amt=bal,date=temp_family.interest_date,interest_apply_date = temp_family.interest_date)
                                    
                bal_sheet=PeopleInterestBalanceSheet.objects.create(management_profile=management,interest=temp_family,
                            principal_amt=temp_family.principal_amt,credit_amt=bal,balance_amt=bal,date=temp_family.interest_date,interest_apply_date = temp_family.interest_date)
                if temp_family.interest_category == "Interest" : 
                    bal_sheet.principal_balance = temp_family.principal_amt
                    if temp_family.apply_first_interest ==True:
                        bal_sheet.debit_amt = temp_family.interest_amt
                        bal_sheet.intrest_amt = temp_family.interest_amt
                        bal_sheet.intrest_paid_amt = temp_family.interest_amt
                        bal_sheet.save()
                    bal_sheet.save()
                elif temp_family.interest_category == "Interest with capital" : 
                    bal_sheet.principal_balance = temp_family.principal_amt
                    if temp_family.apply_first_interest ==True:
                        bal_sheet.debit_amt = temp_family.interest_amt
                        bal_sheet.intrest_amt = temp_family.interest_amt
                        bal_sheet.intrest_paid_amt = temp_family.interest_amt
                        bal_sheet.save()
                    bal_sheet.save()
                elif temp_family.interest_category == "Installment Interest" : 
                    bal_sheet.principal_balance = bal
                    if temp_family.apply_first_interest ==True:
                        temp_family.paid_counts= int(temp_family.paid_counts) + 1
                        temp_family.save()
                    bal_sheet.save()
              
                if temp_family.apply_first_interest ==True:
                    bal_sheet.first_interest_apply = True
                    bal_sheet.save()

                if temp_family.nominee_apply == False and rejin.is_superuser == False and rejin.member != None:
                    mem_obj= Member_Details.objects.get(id=rejin.member.id)
                    temp_family.nominee_member_name=mem_obj.member_name
                    temp_family.nominee_member=mem_obj
                    temp_family.nominee_mobile_no=mem_obj.member_mobile_number
                    temp_family.nominee_address=mem_obj.family.address
                    temp_family.save()
                InterestPeopleReport.objects.create(management_profile=management,interest=temp_family,reportdate=temp_family.interest_date,credit_amt=bal,balance_amt=bal,type_choice="Initial",created_by =rejin.id)
                if temp_family.apply_first_interest == True:
                    new_interest_report = InterestPeopleReport.objects.create(debit_amt=temp_family.interest_amt,credit_amt=temp_family.interest_amt,management_profile=management,interest=temp_family,reportdate=temp_family.interest_date,balance_amt=bal_sheet.balance_amt,type_choice="Interest",created_by =rejin.id)
                    
                    
                # Bug fix: previously this only ran when interest_date is in the
                # current calendar year and a previous month of the same year,
                # which silently skipped penalty/interest application for
                # records created in earlier years.  We now run whenever the
                # interest_date is at least one full month in the past.
                from dateutil.relativedelta import relativedelta as _rdelta
                if date_object + _rdelta(months=1) <= datetime.date.today():
                   
                    inter_check=PeopleInterestDetails.objects.filter(id=temp_family.id).first()
                    inter_bal = PeopleInterestBalanceSheet.objects.get(interest_id=inter_check.id)
                    if interest_type=="Management Interest":
                        # if inter_check.interest_category == "Installment Interest" :   
                        #     pass
                        # else: 
                            checking_dates=temp_family.interest_date + relativedelta(months=1)
                            checking_day=datetime.date(checking_dates.year,checking_dates.month,5)
                            checking_day_penalty=datetime.date(checking_dates.year,checking_dates.month,20)


                            if checking_day <= datetime.date.today():
                                if inter_check.interest_type_new == "amount":
                                    inter_bal.intrest_amt = float(inter_bal.intrest_amt) + float(inter_check.fix_interest_rate_percent)
                                    inter_bal.intrest_balance_amt = float(inter_bal.intrest_balance_amt) + float(inter_check.fix_interest_rate_percent)
                                    inter_bal.credit_amt = float(inter_bal.credit_amt) + float(inter_check.fix_interest_rate_percent)
                                    inter_bal.balance_amt = float(inter_bal.balance_amt) + float(inter_check.fix_interest_rate_percent)
                                    inter_bal.save()
                                    InterestPeopleReport.objects.create(management_profile=inter_check.management_profile,interest=inter_check,reportdate=checking_day,credit_amt=inter_check.fix_interest_rate_percent,balance_amt=inter_bal.balance_amt,type_choice="Interest",created_by=inter_check.created_by)

                                elif inter_check.interest_type_new == "percentage":
                                    interest_convert=(float(inter_bal.principal_balance) * float(inter_check.fix_interest_rate_percent))/100
                                    inter_bal.intrest_amt = float(inter_bal.intrest_amt) + float(interest_convert)
                                    inter_bal.intrest_balance_amt = float(inter_bal.intrest_balance_amt) + float(interest_convert)
                                    inter_bal.credit_amt = float(inter_bal.credit_amt) + float(interest_convert)
                                    inter_bal.balance_amt = float(inter_bal.balance_amt) + float(interest_convert)
                                    inter_bal.save()
                                    InterestPeopleReport.objects.create(management_profile=inter_check.management_profile,interest=inter_check,reportdate=checking_day,credit_amt=interest_convert,balance_amt=inter_bal.balance_amt,type_choice="Interest",created_by=inter_check.created_by)
                                    
                                if datetime.date.today() >= checking_day_penalty:
                                    if inter_check.penalty_type == "percentage":
                                        per_convert=(float(inter_bal.intrest_balance_amt) * float(inter_check.penalty_amount))/100
                                        inter_bal.penalty_balance_amt = float(inter_bal.penalty_balance_amt) + float(per_convert)
                                        inter_bal.penalty_amt = float(inter_bal.penalty_amt) + float(per_convert)
                                        inter_bal.credit_amt = float(inter_bal.credit_amt) + float(per_convert)
                                        inter_bal.balance_amt = float(inter_bal.balance_amt) + float(per_convert)
                                        inter_bal.save()
                                        InterestPeopleReport.objects.create(management_profile=inter_check.management_profile,interest=inter_check,reportdate=datetime.date.today(),credit_amt=float(per_convert),balance_amt=inter_bal.balance_amt,type_choice="Penalty",created_by=inter_check.created_by)
                                    elif inter_check.penalty_type== "amount":
                                        inter_bal.penalty_balance_amt = float(inter_bal.penalty_balance_amt) + float(inter_check.penalty_amount)
                                        inter_bal.penalty_amt = float(inter_bal.penalty_amt) + float(inter_check.penalty_amount)
                                        inter_bal.credit_amt = float(inter_bal.credit_amt) + float(inter_check.penalty_amount)
                                        inter_bal.balance_amt = float(inter_bal.balance_amt) + float(inter_check.penalty_amount)
                                        inter_bal.save()
                                        InterestPeopleReport.objects.create(management_profile=inter_check.management_profile,interest=inter_check,reportdate=datetime.date.today(),credit_amt=inter_check.penalty_amount,balance_amt=inter_bal.balance_amt,type_choice="Penalty",created_by=inter_check.created_by)
                                
                                inter_bal.interest_apply_date=checking_day
                                inter_bal.save() 
                            # elif checking_day < datetime.date.today():
                            #     if inter_check.interest_type_new == "amount":
                            #         inter_bal.intrest_amt = float(inter_bal.intrest_amt) + float(inter_check.fix_interest_rate_percent)
                            #         inter_bal.intrest_balance_amt = float(inter_bal.intrest_balance_amt) + float(inter_check.fix_interest_rate_percent)
                            #         inter_bal.credit_amt = float(inter_bal.credit_amt) + float(inter_check.fix_interest_rate_percent)
                            #         inter_bal.balance_amt = float(inter_bal.balance_amt) + float(inter_check.fix_interest_rate_percent)
                            #         inter_bal.save()
                            #         InterestPeopleReport.objects.create(management_profile=inter_check.management_profile,interest=inter_check,reportdate=checking_day,credit_amt=inter_check.fix_interest_rate_percent,balance_amt=inter_bal.balance_amt,type_choice="Interest",created_by=inter_check.created_by)

                            #     elif inter_check.interest_type_new == "percentage":
                            #         interest_convert=(float(inter_bal.principal_balance) * float(inter_check.fix_interest_rate_percent))/100
                            #         inter_bal.intrest_amt = float(inter_bal.intrest_amt) + float(interest_convert)
                            #         inter_bal.intrest_balance_amt = float(inter_bal.intrest_balance_amt) + float(interest_convert)
                            #         inter_bal.credit_amt = float(inter_bal.credit_amt) + float(interest_convert)
                            #         inter_bal.balance_amt = float(inter_bal.balance_amt) + float(interest_convert)
                            #         inter_bal.save()
                            #         InterestPeopleReport.objects.create(management_profile=inter_check.management_profile,interest=inter_check,reportdate=checking_day,credit_amt=interest_convert,balance_amt=inter_bal.balance_amt,type_choice="Interest",created_by=inter_check.created_by)
                                
                                # if inter_check.penalty_type == "percentage":
                                #     per_convert=(float(inter_bal.intrest_balance_amt) * float(inter_check.penalty_amount))/100
                                #     inter_bal.penalty_balance_amt = float(inter_bal.penalty_balance_amt) + float(per_convert)
                                #     inter_bal.penalty_amt = float(inter_bal.penalty_amt) + float(per_convert)
                                #     inter_bal.credit_amt = float(inter_bal.credit_amt) + float(per_convert)
                                #     inter_bal.balance_amt = float(inter_bal.balance_amt) + float(per_convert)
                                #     inter_bal.save()
                                #     InterestPeopleReport.objects.create(management_profile=inter_check.management_profile,interest=inter_check,reportdate=datetime.date.today(),credit_amt=float(per_convert),balance_amt=inter_bal.balance_amt,type_choice="Penalty",created_by=inter_check.created_by)
                                # elif inter_check.penalty_type== "amount":
                                #     inter_bal.penalty_balance_amt = float(inter_bal.penalty_balance_amt) + float(inter_check.penalty_amount)
                                #     inter_bal.penalty_amt = float(inter_bal.penalty_amt) + float(inter_check.penalty_amount)
                                #     inter_bal.credit_amt = float(inter_bal.credit_amt) + float(inter_check.penalty_amount)
                                #     inter_bal.balance_amt = float(inter_bal.balance_amt) + float(inter_check.penalty_amount)
                                #     inter_bal.save()
                                #     InterestPeopleReport.objects.create(management_profile=inter_check.management_profile,interest=inter_check,reportdate=datetime.date.today(),credit_amt=inter_check.penalty_amount,balance_amt=inter_bal.balance_amt,type_choice="Penalty",created_by=inter_check.created_by)
                            
                                inter_bal.interest_apply_date=checking_day
                                inter_bal.save()
                                
                    elif interest_type=="Chit fund Interest":        
                       
                            checking_dates=temp_family.interest_date + relativedelta(months=1)
                            checking_day=datetime.date(checking_dates.year,checking_dates.month,1)
                            checking_day_penalty=datetime.date(checking_dates.year,checking_dates.month,20)


                            if checking_day > datetime.date.today():
                                if inter_check.interest_type_new == "amount":
                                    inter_bal.intrest_amt = float(inter_bal.intrest_amt) + float(inter_check.fix_interest_rate_percent)
                                    inter_bal.intrest_balance_amt = float(inter_bal.intrest_balance_amt) + float(inter_check.fix_interest_rate_percent)
                                    inter_bal.credit_amt = float(inter_bal.credit_amt) + float(inter_check.fix_interest_rate_percent)
                                    inter_bal.balance_amt = float(inter_bal.balance_amt) + float(inter_check.fix_interest_rate_percent)
                                    inter_bal.save()
                                    InterestPeopleReport.objects.create(management_profile=inter_check.management_profile,interest=inter_check,reportdate=checking_day,credit_amt=inter_check.fix_interest_rate_percent,balance_amt=inter_bal.balance_amt,type_choice="Interest",created_by=inter_check.created_by)

                                elif inter_check.interest_type_new == "percentage":
                                    interest_convert=(float(inter_bal.principal_balance) * float(inter_check.fix_interest_rate_percent))/100
                                    inter_bal.intrest_amt = float(inter_bal.intrest_amt) + float(interest_convert)
                                    inter_bal.intrest_balance_amt = float(inter_bal.intrest_balance_amt) + float(interest_convert)
                                    inter_bal.credit_amt = float(inter_bal.credit_amt) + float(interest_convert)
                                    inter_bal.balance_amt = float(inter_bal.balance_amt) + float(interest_convert)
                                    inter_bal.save()
                                    InterestPeopleReport.objects.create(management_profile=inter_check.management_profile,interest=inter_check,reportdate=checking_day,credit_amt=interest_convert,balance_amt=inter_bal.balance_amt,type_choice="Interest",created_by=inter_check.created_by)
                                    
                                inter_bal.interest_apply_date=checking_day
                                inter_bal.save()

                            elif checking_day <= datetime.date.today():
                                if inter_check.interest_type_new == "amount":
                                    inter_bal.intrest_amt = float(inter_bal.intrest_amt) + float(inter_check.fix_interest_rate_percent)
                                    inter_bal.intrest_balance_amt = float(inter_bal.intrest_balance_amt) + float(inter_check.fix_interest_rate_percent)
                                    inter_bal.credit_amt = float(inter_bal.credit_amt) + float(inter_check.fix_interest_rate_percent)
                                    inter_bal.balance_amt = float(inter_bal.balance_amt) + float(inter_check.fix_interest_rate_percent)
                                    inter_bal.save()
                                    InterestPeopleReport.objects.create(management_profile=inter_check.management_profile,interest=inter_check,reportdate=checking_day,credit_amt=inter_check.fix_interest_rate_percent,balance_amt=inter_bal.balance_amt,type_choice="Interest",created_by=inter_check.created_by)

                                elif inter_check.interest_type_new == "percentage":
                                    interest_convert=(float(inter_bal.principal_balance) * float(inter_check.fix_interest_rate_percent))/100
                                    inter_bal.intrest_amt = float(inter_bal.intrest_amt) + float(interest_convert)
                                    inter_bal.intrest_balance_amt = float(inter_bal.intrest_balance_amt) + float(interest_convert)
                                    inter_bal.credit_amt = float(inter_bal.credit_amt) + float(interest_convert)
                                    inter_bal.balance_amt = float(inter_bal.balance_amt) + float(interest_convert)
                                    inter_bal.save()
                                    InterestPeopleReport.objects.create(management_profile=inter_check.management_profile,interest=inter_check,reportdate=checking_day,credit_amt=interest_convert,balance_amt=inter_bal.balance_amt,type_choice="Interest",created_by=inter_check.created_by)
                                
                                if datetime.date.today() >= checking_day_penalty:
                                    if inter_check.penalty_type == "percentage":
                                        per_convert=(float(inter_bal.intrest_balance_amt) * float(inter_check.penalty_amount))/100
                                        inter_bal.penalty_balance_amt = float(inter_bal.penalty_balance_amt) + float(per_convert)
                                        inter_bal.penalty_amt = float(inter_bal.penalty_amt) + float(per_convert)
                                        inter_bal.credit_amt = float(inter_bal.credit_amt) + float(per_convert)
                                        inter_bal.balance_amt = float(inter_bal.balance_amt) + float(per_convert)
                                        inter_bal.save()
                                        InterestPeopleReport.objects.create(management_profile=inter_check.management_profile,interest=inter_check,reportdate=datetime.date.today(),credit_amt=float(per_convert),balance_amt=inter_bal.balance_amt,type_choice="Penalty",created_by=inter_check.created_by)
                                    elif inter_check.penalty_type== "amount":
                                        inter_bal.penalty_balance_amt = float(inter_bal.penalty_balance_amt) + float(inter_check.penalty_amount)
                                        inter_bal.penalty_amt = float(inter_bal.penalty_amt) + float(inter_check.penalty_amount)
                                        inter_bal.credit_amt = float(inter_bal.credit_amt) + float(inter_check.penalty_amount)
                                        inter_bal.balance_amt = float(inter_bal.balance_amt) + float(inter_check.penalty_amount)
                                        inter_bal.save()
                                        InterestPeopleReport.objects.create(management_profile=inter_check.management_profile,interest=inter_check,reportdate=datetime.date.today(),credit_amt=inter_check.penalty_amount,balance_amt=inter_bal.balance_amt,type_choice="Penalty",created_by=inter_check.created_by)
                                    
                                inter_bal.interest_apply_date=checking_day
                                inter_bal.save()
                    
                return Response(serializer876.data,status=status.HTTP_201_CREATED)
            else:
                return Response(serializer876.errors,status=status.HTTP_400_BAD_REQUEST)
        return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)
    
    elif request.method == 'GET':
        our_family = PeopleInterestDetails.objects.filter(management_profile=management)
        # our_family = PeopleInterestDetails.objects.all()
        serializer = PeopleInterestDetailsSerializer(our_family,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)

        
        
@api_view(['GET','PUT','PATCH',"DELETE"])
def edit_interest_given_details(request,pk):
    rejin=token_checking(request)
    if not rejin:
        return Response({"message":"No User Found"},status=status.HTTP_401_UNAUTHORIZED)
    if not rejin.is_active:
        return Response({"message":"Not Authorized Please Contact Admin"},status=status.HTTP_401_UNAUTHORIZED)
    get_role=rejin.user_role
    if rejin.my_role!=None:
        permiss=Permisions.objects.filter(role_link_id=rejin.my_role.id).first()
        if permiss:
            perm=Permisions.objects.get(role_link_id=rejin.my_role.id)
    try:
        customer = PeopleInterestDetails.objects.get(pk=pk)  
        interest_type=customer.interest_type
    except PeopleInterestDetails.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    check_management=ManagementDetails.objects.all()
    if not check_management:
        dict6={}
        dict6['message']= "First Add Management Profile details"
        return Response(dict6,status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        management=ManagementDetails.objects.all().first()
    
    if request.method == 'GET':
        serializer = PeopleInterestDetailsSerializer(customer)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    elif request.method == 'PUT': 
        if get_role=="User" and perm.interest_edit ==True or get_role=="Admin" or rejin.is_superuser == True:   
            check_blansheet=PeopleInterestBalanceSheet.objects.filter(management_profile=management,interest=customer)
            if len(check_blansheet)>1:
                dict6={}
                dict6['message']= "Payment happening"
                return Response(dict6,status=status.HTTP_406_NOT_ACCEPTABLE)
            interest_type= customer.interest_type
            if interest_type=="Management Interest":
                managefil=ManagementTreasure.objects.filter(management_profile=management)
                if managefil:
                    manage=ManagementTreasure.objects.get(management_profile=management)
                    if (float(manage.cash_in_hand)-float(manage.expence_amt)) < float(customer.principal_amt):
                        msg={'msg':'Insufficient amount in cash in hand'}
                        return Response(msg,status=status.HTTP_226_IM_USED)
            elif interest_type=="Chit fund Interest":
                chit_fund_obj= ChitFundsDetails.objects.filter(id=customer.chitt_fund.id)
                if chit_fund_obj:
                    chit_fund_get=ChitFundsDetails.objects.get(id=customer.chitt_fund.id)
                    if float(chit_fund_get.cash_inhand_amount) < customer.principal_amt:
                        msg={'msg':'Insufficient amount in chit fund'}
                        return Response(msg,status=status.HTTP_226_IM_USED)

            serializer876 = PeopleInterestDetailsSerializer(customer,data=request.data)
            if serializer876.is_valid():
         
                if interest_type=="Management Interest":
                    managefilter=ManagementTreasure.objects.filter(management_profile=management)
                    if managefilter:
                        manage_get=ManagementTreasure.objects.get(management_profile=management)
                        # manage_get.cash_in_hand = float(manage_get.cash_in_hand) - float(temp_family.principal_amt)
                        manage_get.expence_amt = float(manage_get.expence_amt) - float(temp_family.principal_amt)
                        manage_get.save()
                   
                elif interest_type=="Chit fund Interest":
                    chit_fund_object= ChitFundsDetails.objects.filter(id=temp_family.chitt_fund.id)
                    if chit_fund_object:
                        chit_fund_get_new=ChitFundsDetails.objects.get(id=temp_family.chitt_fund.id)
                        chit_fund_get_new.cash_inhand_amount=float(chit_fund_get_new.cash_inhand_amount) + float(request.data['principal_amt'])
                        chit_fund_get_new.principal_given_amount=float(chit_fund_get_new.principal_given_amount) - float(request.data['principal_amt'])
                        chit_fund_get_new.save()        
                
                temp_family=serializer876.save()
                temp_family.created_by=rejin.id
                temp_family.save()
                
                if temp_family.first_interest_amt !=None:
                    pay=float(temp_family.first_interest_amt)
                else:
                    pay=0
                
                bal=float(temp_family.principal_amt)-pay  
                
                check_bal_sheet=PeopleInterestBalanceSheet.objects.filter(interest=customer).first()
                check_bal_sheet.credit_amt=temp_family.principal_amt
                check_bal_sheet.debit_amt=pay
                check_bal_sheet.balance_amt=bal
                check_bal_sheet.save()
                if temp_family.first_interest_amt !=None:
                    check_bal_sheet.first_interest_apply = True
                    check_bal_sheet.save()
                else:
                    check_bal_sheet.first_interest_apply = False
                    check_bal_sheet.save()
                if temp_family.nominee_apply == False and rejin.is_superuser == False:
                    mem_obj= Member_Details.objects.get(id=rejin.member.id)
                    temp_family.nominee_member_name=mem_obj.member_name
                    temp_family.nominee_member=mem_obj
                    temp_family.nominee_mobile_no=mem_obj.member_mobile_number
                    temp_family.nominee_address=mem_obj.family.address
                    temp_family.save()
                else:
                    temp_family.nominee_member_name=None
                    temp_family.nominee_member=None
                    temp_family.nominee_mobile_no=None
                    temp_family.nominee_address=None
                    temp_family.save()     

                return Response(serializer876.data,status=status.HTTP_201_CREATED)
            else:
                return Response(serializer876.errors,status=status.HTTP_400_BAD_REQUEST)
        return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)
    
    elif request.method == 'PATCH': 
        if get_role=="User" and perm.interest_edit ==True or get_role=="Admin" or rejin.is_superuser == True:   
            serializer876 = PeopleInterestDetailsSerializer(customer,data=request.data,partial=True)
            if serializer876.is_valid():
                temp_family=serializer876.save()
                temp_family.created_by=rejin.id
                temp_family.save()
                return Response(serializer876.data,status=status.HTTP_201_CREATED)
            else:
                return Response(serializer876.errors,status=status.HTTP_400_BAD_REQUEST)
        return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)
            
    elif request.method == 'DELETE':
        if get_role=="User" and perm.interest_del ==True or get_role=="Admin" or rejin.is_superuser == True or get_role=="User" and perm.interest_edit ==True: 
            # interest_type= request.data['interest_type']
            # if interest_type=="Management Interest":
            #     managefil=ManagementTreasure.objects.filter(management_profile=management)
            #     if managefil:
            #         manage=ManagementTreasure.objects.get(management_profile=management)
            #         if (float(manage.cash_in_hand)-float(manage.expence_amt)) < float(request.data['principal_amt']):
            #             return Response(status=status.HTTP_226_IM_USED)
            # elif interest_type=="Chit fund Interest":
            #     chit_fund_obj= ChitFundsDetails.objects.filter(id=request.data['chitt_fund'])
            #     if chit_fund_obj:
            #         chit_fund_get=ChitFundsDetails.objects.get(id=request.data['chitt_fund'])
            #         if float(chit_fund_get.cash_inhand_amount) < float(request.data['principal_amt']):
            #             return Response(status=status.HTTP_226_IM_USED)
            # inter_report=InterestPeopleReport.objects.filter(interest=customer,management_profile=management)      
            # if inter_report:
            #     inter_report_get=InterestPeopleReport.objects.filter(interest=customer,management_profile=management).last()
            #     inter_fil=InterestPeopleReport.objects.filter(id__gt=inter_report_get.id,interest=customer,management_profile=management)  
            #     if inter_fil:
            #         msg={'msg':'interest can not be deleted'}
            #         return Response(status=status.HTTP_226_IM_USED)
            collection_obj=CollectionDetails.objects.filter(interest=customer,management_profile=management)
            if collection_obj:
                    msg={'msg':'interest can not be deleted as it involved in transactions'}
                    return Response(msg,status=status.HTTP_226_IM_USED)
            if customer.interest_type=="Management Interest":
                managefilter=ManagementTreasure.objects.filter(management_profile=management)
                if managefilter:
                    manage_get=ManagementTreasure.objects.get(management_profile=management)
                    # manage_get.cash_in_hand = flo*at(manage_get.cash_in_hand) - float(temp_family.principal_amt)
                    manage_get.expence_amt = float(manage_get.expence_amt) - float(customer.principal_amt)
                    manage_get.save()
            
            elif customer.interest_type=="Chit fund Interest":
                chit_fund_object= ChitFundsDetails.objects.filter(id=customer.chitt_fund.id)
                if chit_fund_object:
                    chit_fund_get_new=ChitFundsDetails.objects.get(id=customer.chitt_fund.id)
                    chit_fund_get_new.cash_inhand_amount=float(chit_fund_get_new.cash_inhand_amount) + float(customer.principal_amt)
                    chit_fund_get_new.principal_given_amount=float(chit_fund_get_new.principal_given_amount) - float(customer.principal_amt)
                    chit_fund_get_new.save()
            customer.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)
    
@api_view(['GET'])
def management_interest_details_table(request):
    rejin=token_checking(request)
    if not rejin:
        return Response({"message":"No User Found"},status=status.HTTP_401_UNAUTHORIZED)
    if not rejin.is_active:
        return Response({"message":"Not Authorized Please Contact Admin"},status=status.HTTP_401_UNAUTHORIZED)
    
    check_management=ManagementDetails.objects.all()
    if not check_management:
        dict6={}
        dict6['message']= "First Add Management Profile details"
        return Response(dict6,status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        management=ManagementDetails.objects.all().first()

    if request.method == 'GET':
        our_family = PeopleInterestDetails.objects.filter(management_profile=management,interest_type='Management Interest',interest_category="Interest")
        serializer = PeopleInterestDetailsSerializer(our_family,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
@api_view(['GET'])
def management_capital_interest_details_table(request):
    rejin=token_checking(request)
    if not rejin:
        return Response({"message":"No User Found"},status=status.HTTP_401_UNAUTHORIZED)
    if not rejin.is_active:
        return Response({"message":"Not Authorized Please Contact Admin"},status=status.HTTP_401_UNAUTHORIZED)
    
    check_management=ManagementDetails.objects.all()
    if not check_management:
        dict6={}
        dict6['message']= "First Add Management Profile details"
        return Response(dict6,status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        management=ManagementDetails.objects.all().first()

    if request.method == 'GET':
        our_family = PeopleInterestDetails.objects.filter(management_profile=management,interest_type='Management Interest',interest_category="Interest with capital")
        serializer = PeopleInterestDetailsSerializer(our_family,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)    

@api_view(['GET'])
def management_installment_interest_details_table(request):
    rejin=token_checking(request)
    if not rejin:
        return Response({"message":"No User Found"},status=status.HTTP_401_UNAUTHORIZED)
    if not rejin.is_active:
        return Response({"message":"Not Authorized Please Contact Admin"},status=status.HTTP_401_UNAUTHORIZED)
    
    check_management=ManagementDetails.objects.all()
    if not check_management:
        dict6={}
        dict6['message']= "First Add Management Profile details"
        return Response(dict6,status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        management=ManagementDetails.objects.all().first()

    if request.method == 'GET':
        our_family = PeopleInterestDetails.objects.filter(management_profile=management,interest_type='Management Interest',interest_category="Installment Interest")
        serializer = PeopleInterestDetailsSerializer(our_family,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)    


@api_view(['GET'])
def chit_fund_interest_details_table(request):
    rejin=token_checking(request)
    if not rejin:
        return Response({"message":"No User Found"},status=status.HTTP_401_UNAUTHORIZED)
    if not rejin.is_active:
        return Response({"message":"Not Authorized Please Contact Admin"},status=status.HTTP_401_UNAUTHORIZED)
    
    check_management=ManagementDetails.objects.all()
    if not check_management:
        dict6={}
        dict6['message']= "First Add Management Profile details"
        return Response(dict6,status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        management=ManagementDetails.objects.all().first()

    if request.method == 'GET':
        our_family = PeopleInterestDetails.objects.filter(management_profile=management,interest_type='Chit fund Interest',interest_category="Interest")
        serializer = PeopleInterestDetailsSerializer(our_family,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)    

@api_view(['GET'])
def chit_fund_capitalinterest_details_table(request):
    rejin=token_checking(request)
    if not rejin:
        return Response({"message":"No User Found"},status=status.HTTP_401_UNAUTHORIZED)
    if not rejin.is_active:
        return Response({"message":"Not Authorized Please Contact Admin"},status=status.HTTP_401_UNAUTHORIZED)
    
    check_management=ManagementDetails.objects.all()
    if not check_management:
        dict6={}
        dict6['message']= "First Add Management Profile details"
        return Response(dict6,status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        management=ManagementDetails.objects.all().first()

    if request.method == 'GET':
        our_family = PeopleInterestDetails.objects.filter(management_profile=management,interest_type='Chit fund Interest',interest_category="Interest with capital")
        serializer = PeopleInterestDetailsSerializer(our_family,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)    

@api_view(['GET'])
def chit_fund_installment_interest_details_table(request):
    rejin=token_checking(request)
    if not rejin:
        return Response({"message":"No User Found"},status=status.HTTP_401_UNAUTHORIZED)
    if not rejin.is_active:
        return Response({"message":"Not Authorized Please Contact Admin"},status=status.HTTP_401_UNAUTHORIZED)
    
    check_management=ManagementDetails.objects.all()
    if not check_management:
        dict6={}
        dict6['message']= "First Add Management Profile details"
        return Response(dict6,status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        management=ManagementDetails.objects.all().first()

    if request.method == 'GET':
        our_family = PeopleInterestDetails.objects.filter(management_profile=management,interest_type='Chit fund Interest',interest_category="Installment Interest")
        
        serializer = PeopleInterestDetailsSerializer(our_family,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)    



@api_view(['GET'])
def interest_profile(request, pk):
    print('Fetching Interest Profile...')

    rejin = token_checking(request)
    if not rejin:
        return Response({"message": "No User Found"}, status=status.HTTP_401_UNAUTHORIZED)
    if not rejin.is_active:
        return Response({"message": "Not Authorized. Please Contact Admin"}, status=status.HTTP_401_UNAUTHORIZED)

    management = ManagementDetails.objects.first()
    if not management:
        return Response({"message": "Management Profile details not found"}, status=status.HTTP_406_NOT_ACCEPTABLE)

    mer = PeopleInterestDetails.objects.filter(pk=pk, management_profile=management).first()
    if not mer:
        return Response({"message": "Interest profile not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer1 = PeopleInterestDetailsSerializer(mer)
    coll_obj = CollectionDetails.objects.filter(management_profile=management, interest=mer)
    serializer5 = CollectionDetailsSerializer(coll_obj, many=True)

    balsheet_objts = PeopleInterestBalanceSheet.objects.filter(management_profile=management, interest=mer)
    ser2 = PeopleInterestBalanceSheetSerializer(balsheet_objts, many=True)

    total_amount_obj = PeopleInterestBalanceSheet.objects.filter(
        interest=mer, management_profile=management
    ).aggregate(total_amount=Sum('balance_amt'))

    total_amount_value = total_amount_obj.get('total_amount', 0) if total_amount_obj else 0

    report = InterestPeopleReport.objects.filter(management_profile=management, interest=mer)
    report_ser = InterestPeopleReportserializer(report, many=True)

    chit_fund_balance_sheet = ChitFundInterestOverallReport.objects.filter(management_profile=management, interest=mer)
    chit_fund_balance_sheet_ser = ChitFundInterestOverallReport_serializer(chit_fund_balance_sheet, many=True)

    response_data = {
        "profile": serializer1.data,
        "balance_sheet": ser2.data,
        "paid_histry": serializer5.data,
        "total_amt": total_amount_value,
        "report_ser": report_ser.data,
        "chit_fund_balance_sheet": chit_fund_balance_sheet_ser.data
    }

  
    return Response(response_data, status=status.HTTP_200_OK)


from family.models import Member_Details
from family.serializers import member_DetailsSerializer

@api_view(['GET','POST'])
def interest_member_list(request):
    rejin=token_checking(request)
    if not rejin:
        return Response({"message":"No User Found"},status=status.HTTP_401_UNAUTHORIZED)
    if not rejin.is_active:
        return Response({"message":"Not Authorized Please Contact Admin"},status=status.HTTP_401_UNAUTHORIZED)
    
    check_management=ManagementDetails.objects.all()
    if not check_management:
        dict6={}
        dict6['message']= "First Add Management Profile details"
        return Response(dict6,status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        management=ManagementDetails.objects.all().first()
    if request.method == "GET":
        coll_obj=Member_Details.objects.filter(member_tax_eligible=True,death=False,action=True,adult=True)
        list_new=[]
        for i in coll_obj:
            dic={}
            family=Fammily_Details.objects.get(id=i.family.id)
            family_ser=Fammily_DetailsSerializer(family)
            serializer = member_DetailsSerializer(i)
            dic['member'] =serializer.data
            dic['address'] =i.family.address
            list_new.append(dic)

        return Response(list_new,status=status.HTTP_200_OK)




from chit_fund.serializers import ChitFundsDetailsSerializer

@api_view(['GET','POST'])
def get_chit_fund_details(request):
    rejin=token_checking(request)
    if not rejin:
        return Response({"message":"No User Found"},status=status.HTTP_401_UNAUTHORIZED)
    if not rejin.is_active:
        return Response({"message":"Not Authorized Please Contact Admin"},status=status.HTTP_401_UNAUTHORIZED)
    
    check_management=ManagementDetails.objects.all()
    if not check_management:
        dict6={}
        dict6['message']= "First Add Management Profile details"
        return Response(dict6,status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        management=ManagementDetails.objects.all().first()

    if request.method == 'GET':
        our_family = ChitFundsDetails.objects.filter(management_profile=management,action=True)
        serializer = ChitFundsDetailsSerializer(our_family,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)   
    



@api_view(['GET','POST'])
def chit_interest_filter_based_type(request):
    rejin=token_checking(request)
    if not rejin:
        return Response({"message":"No User Found"},status=status.HTTP_401_UNAUTHORIZED)
    if not rejin.is_active:
        return Response({"message":"Not Authorized Please Contact Admin"},status=status.HTTP_401_UNAUTHORIZED)
    
    check_management=ManagementDetails.objects.all()
    if not check_management:
        dict6={}
        dict6['message']= "First Add Management Profile details"
        return Response(dict6,status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        management=ManagementDetails.objects.all().first()
    if request.method == "POST":
        type=request.data['type']
        interest = PeopleInterestDetails.objects.filter(interest_type="Chit fund Interest",interest_category=type,management_profile=management)
        interest_ser=PeopleInterestDetailsSerializer(interest,many=True)
        return Response(interest_ser.data,status=status.HTTP_200_OK)
    



@api_view(['GET','POST'])
def management_interest_filter_based_type(request):
    rejin=token_checking(request)
    if not rejin:
        return Response({"message":"No User Found"},status=status.HTTP_401_UNAUTHORIZED)
    if not rejin.is_active:
        return Response({"message":"Not Authorized Please Contact Admin"},status=status.HTTP_401_UNAUTHORIZED)
    
    check_management=ManagementDetails.objects.all()
    if not check_management:
        dict6={}
        dict6['message']= "First Add Management Profile details"
        return Response(dict6,status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        management=ManagementDetails.objects.all().first()
    if request.method == "POST":
        type=request.data['type']
        interest = PeopleInterestDetails.objects.filter(interest_type="Management Interest",interest_category=type,management_profile=management)
        interest_ser=PeopleInterestDetailsSerializer(interest,many=True)
        return Response(interest_ser.data,status=status.HTTP_200_OK)





@api_view(['GET','POST'])
def interest_people_report_get(request):
    rejin=token_checking(request)
    if not rejin:
        return Response({"message":"No User Found"},status=status.HTTP_401_UNAUTHORIZED)
    if not rejin.is_active:
        return Response({"message":"Not Authorized Please Contact Admin"},status=status.HTTP_401_UNAUTHORIZED)
    
    check_management=ManagementDetails.objects.all()
    if not check_management:
        dict6={}
        dict6['message']= "First Add Management Profile details"
        return Response(dict6,status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        management=ManagementDetails.objects.all().first()
    if request.method == "GET":
        interest = InterestPeopleReport.objects.filter(management_profile=management)
        interest_ser=InterestPeopleReportserializer(interest,many=True)
        return Response(interest_ser.data,status=status.HTTP_200_OK)
    elif request.method == "POST":
        jj=request.data['range']
        end_date=jj['end_date']
        start_date=jj['start_date']

        if start_date and end_date:
            start_date_time_obj = datetime.datetime.strptime(str(start_date), '%Y-%m-%d').date()
            end_date_time_obj = datetime.datetime.strptime(str(end_date), '%Y-%m-%d').date()
            interest = InterestPeopleReport.objects.filter(management_profile=management,reportdate__gte=start_date_time_obj,reportdate__lte=end_date_time_obj)
            interest_ser=InterestPeopleReportserializer(interest,many=True)
            return Response(interest_ser.data,status=status.HTTP_200_OK)
        

@api_view(['GET','POST'])
def interest_people_balance_get(request):
    rejin=token_checking(request)
    if not rejin:
        return Response({"message":"No User Found"},status=status.HTTP_401_UNAUTHORIZED)
    if not rejin.is_active:
        return Response({"message":"Not Authorized Please Contact Admin"},status=status.HTTP_401_UNAUTHORIZED)
    
    check_management=ManagementDetails.objects.all()
    if not check_management:
        dict6={}
        dict6['message']= "First Add Management Profile details"
        return Response(dict6,status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        management=ManagementDetails.objects.all().first()
    if request.method == "POST":
        interest_type=request.data['interest_type']
        category=request.data['category']
        interest_balance=PeopleInterestBalanceSheet.objects.filter(interest__interest_category=category,interest__interest_type=interest_type,management_profile=management,intrest_balance_amt__gt=0)
        serializer=PeopleInterestssssBalanceSheetSerializer(interest_balance,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    
# def calculate_payment_amount(request):


@api_view(['GET','POST'])
def interest_people_installmentinterest_balance_get(request):
    rejin=token_checking(request)
    if not rejin:
        return Response({"message":"No User Found"},status=status.HTTP_401_UNAUTHORIZED)
    if not rejin.is_active:
        return Response({"message":"Not Authorized Please Contact Admin"},status=status.HTTP_401_UNAUTHORIZED)
    
    check_management=ManagementDetails.objects.all()
    if not check_management:
        dict6={}
        dict6['message']= "First Add Management Profile details"
        return Response(dict6,status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        management=ManagementDetails.objects.all().first()
    if request.method == "POST":
        interest_type=request.data['interest_type']
        category=request.data['category']
        interest_period=request.data['interest_period']
        interest_balance=PeopleInterestBalanceSheet.objects.filter(interest__interest_type=interest_type,management_profile=management,interest__interest_category=category,interest__interest_period_type=interest_period)
        out=[]
        if interest_period=="Week":
            for iii in interest_balance:
                if iii.interest.interest_period != iii.interest.paid_counts:  
      

                    date_check=iii.interest.interest_date + relativedelta(weeks=iii.interest.paid_counts)
                    limit_date_check=iii.interest.interest_date + relativedelta(weeks=iii.interest.interest_period )

                    da=datetime.date.today()

                    if date_check <=da  and date_check <= limit_date_check:

                        if iii.balance_amt>0 or iii.penalty_balance_amt > 0:    
                            out.append(iii)         
                else:
                    if iii.penalty_balance_amt > 0:
                        out.append(iii)



        elif interest_period=="Days":  
            for iii in interest_balance:
                try:
                    if iii.interest.interest_period != iii.interest.paid_counts:                                       
                        date_check=iii.interest.interest_date + relativedelta(days=iii.interest.paid_counts)
                        limit_date_check=iii.interest.interest_date + relativedelta(days=iii.interest.interest_period )
          
                        if date_check <= datetime.date.today() and date_check <= limit_date_check:                       
                            if iii.balance_amt>0 or iii.penalty_balance_amt > 0:
                                out.append(iii)
                    else:
                        if iii.penalty_balance_amt > 0:
                            out.append(iii)
                except:
                    print("hello")


        elif interest_period=="Month":  
            for iii in interest_balance:
                try:
                    if iii.interest.interest_period != iii.interest.paid_counts:
                        date_check=iii.interest.interest_date + relativedelta(months=iii.interest.paid_counts)
                        limit_date_check=iii.interest.interest_date + relativedelta(months=iii.interest.interest_period )

                        if date_check <= datetime.date.today() and date_check <= limit_date_check:                       
                            if iii.balance_amt>0 or iii.penalty_balance_amt > 0:
                                out.append(iii)
                    else:
                        if iii.penalty_balance_amt > 0:
                            out.append(iii)
                except:
                    print("jjjjjjjjjj")

                                     
        print(out)
        serializer=PeopleInterestssssBalanceSheetSerializer(out,many=True)               
        
        return Response(serializer.data,status=status.HTTP_200_OK)