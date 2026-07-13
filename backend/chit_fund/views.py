from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import jwt
from.serializers import *
from .models import ChitFundsDetails,ChitFundInvesters,ChitFundsettleAplication,ChitFundSettlement,InvestersProfitDistributionTable
from rest_framework.exceptions import AuthenticationFailed
from user.models import User
from user.serializers import RejinUserSerializer78
import pandas as pd
import datetime
from token_app.views import *
from management.models import ManagementDetails
from permisions.models import Permisions
from treasure.models import ManagementTreasure
from interest.models import PeopleInterestDetails
from family.models import Member_Details
from family.serializers import member_DetailsSerializer
from balancesheet.models import PeopleInterestBalanceSheet
from datetime import date
from family.serializers import member_DetailsSerializer
from reports.models import ChitFundInterestOverallReport,Report
from decimal import Decimal
import calendar
from interest.models import PeopleInterestDetails

@api_view(['GET'])
def get_active_chitfunds(request):
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
    if request.method =='GET':
        chit_funds=ChitFundsDetails.objects.filter(management_profile=management,action=True)
        seial9=ChitFundsDetailsSerializer26(chit_funds,many=True)
        return Response(seial9.data,status=status.HTTP_200_OK)


@api_view(['GET'])
def get_chitfund_settlement_application_mem(request):
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
    if request.method =='GET':
        my_list=[]
        chit_funds=ChitFundsDetails.objects.filter(management_profile=management,action=True)
        for chit in chit_funds:
            dict847={}
            seial9=ChitFundsDetailsSerializer26(chit)
            investers=ChitFundInvesters.objects.filter(management_profile=management,chitt_fund=chit,settled=False,action=True)
            serial7=ChitFundInvestersSerializer2(investers,many=True)
            dict847['chit_fund']=seial9.data
            dict847['investers']=serial7.data
            my_list.append(dict847)
        return Response(my_list,status=status.HTTP_200_OK)


@api_view(['GET'])
def get_chitfund_member_details(request):
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
    if request.method =='GET':
       mem= Member_Details.objects.filter(management_profile=management,action=True,death=False,adult=True,marriage_remove=False)
       serializer=member_DetailsSerializer(mem,many=True)
       return Response(serializer.data,status=status.HTTP_200_OK)



@api_view(['GET','POST'])
def management_treasure_get(request):
    rejin=token_checking(request)
    if not rejin:
        return Response({"message":"No User Found"},status=status.HTTP_401_UNAUTHORIZED)
    if not rejin.is_active:
        return Response({"message":"Not Authorized Please Contact Admin"},status=status.HTTP_401_UNAUTHORIZED)
    print(f'token---{rejin}')    
    check_management=ManagementDetails.objects.all()
    if not check_management:
        dict6={}
        dict6['message']= "First Add Management Profile details"
        return Response(dict6,status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        management=ManagementDetails.objects.all().first()   
    if request.method =='GET':
        treasure=ManagementTreasure.objects.filter(management_profile=management).first()
        serializer=ManagementTreasureSerializer(treasure)
        return Response(serializer.data,status=status.HTTP_200_OK)



@api_view(['GET','POST'])
def add_chit_fund(request):
    rejin=token_checking(request)
    if not rejin:
        return Response({"message":"No User Found"},status=status.HTTP_401_UNAUTHORIZED)
    if not rejin.is_active:
        return Response({"message":"Not Authorized Please Contact Admin"},status=status.HTTP_401_UNAUTHORIZED)
    print(f'token---{rejin}')
    
    check_management=ManagementDetails.objects.all()
    if not check_management:
        dict6={}
        dict6['message']= "First Add Management Profile details"
        return Response(dict6,status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        management=ManagementDetails.objects.all().first()
    
    get_role=rejin.user_role
    if rejin.my_role!=None:
        permiss=Permisions.objects.filter(id=rejin.my_role.id).first()
        if permiss:
            perm=Permisions.objects.get(id=rejin.my_role.id)
   
    if request.method =='POST':
        if get_role=="User" and perm.chit_fund_add ==True or get_role=="Admin" or rejin.is_superuser == True: 
            try:
                print('super human')
                print(request.data)
                prod=request.data
                dict87={}
                dict87['chit_name']=prod['chit_name']
                dict87['starting_date']=prod['starting_date']
                dict87['management_amt']=float(prod['management_amt'])
                dict87['management_share_count']=prod["management_share_count"]
                dict87['fixed_chitfund_amount']=prod["fixed_chitfund_amount"]
                # cash=ManagementTreasure.objects.filter(management_profile=management).first().cash_in_hand
                cash=ManagementTreasure.objects.filter(management_profile=management).first()
                if cash:
                    hand_amt=float(cash.cash_in_hand)-float(cash.expence_amt)
                    # if dict87['management_amt']>float(cash):
                    if dict87['management_amt']>float(hand_amt):
                        return Response({"Message":"Entered Amount exceeds the cash in hand amount"},status=status.HTTP_226_IM_USED)
                
                dict87['set_profit_percent']=prod['set_profit_percent']
                dict87['set_intrest_percent']=prod['set_intrest_percent']
                print('godd')
                print(request.data['field_count'])
                print(type(request.data['field_count']))
                pc=int(request.data['field_count'])
                print(pc)
                print(type(pc))
                produ_list=[]
                if pc>=1:
                    for num in range(1,pc+1):
                        dict8={}
                        try:
                            dict8['invester_member']=prod[f"chit[{num}][invester_member]"]
                        except:
                            pass
                        dict8['invester_type']=prod[f"chit[{num}][invester_type]"]
                        dict8['invester_name']=prod[f"chit[{num}][invester_name]"]
                        dict8['invester_address']=prod[f"chit[{num}][invester_address]"]
                        dict8['invester_email']=prod[f"chit[{num}][invester_email]"]
                        dict8['invester_mobile']=prod[f"chit[{num}][invester_mobile]"]
                        dict8['investment_amt']=prod[f"chit[{num}][investment_amt]"]
                        dict8['share_count']=prod[f"chit[{num}][share_count]"]

                        
                        try:
                            dict8['images']=prod[f"chit[{num}][images]"]
                        except:
                            pass
                        try:
                            dict8['documents']=prod[f"chit[{num}][documents]"]
                        except:
                            pass                        
                        produ_list.append(dict8)                        
                dict87['chitt_fund']=produ_list
                print('final')
                print(dict87)
            except:
                return Response({"Message":"Data requirement error"},status=status.HTTP_417_EXPECTATION_FAILED)                    
            serializer876 = ChitFundsDetailsSerializer(data=dict87)
            if serializer876.is_valid():                
                temp_family=serializer876.save()
                temp_family.created_by=rejin.id
                temp_family.management_profile=management
                temp_family.save()
                cash_in=ManagementTreasure.objects.filter(management_profile=management).first()
                cash_in.cash_in_hand -= temp_family.management_amt
                cash_in.save()   
                #pending for create  temple REport  
                ChitFundInterestOverallReport.objects.create(chitfund=temp_family,management_profile=management,amount=temp_family.management_amt,
                                                             income_choice='Investment',managee=True,created_by=rejin.id)
                Report.objects.create(chit_fund=temp_family,management_profile=management,amount=temp_family.management_amt,type_choice='Reduction',created_by=rejin.id)
                get_investers=ChitFundInvesters.objects.filter(first_investers=True,chitt_fund_id=temp_family.id)
                if get_investers:
                    for kk in get_investers:
                        kk.joining_date=datetime.datetime.today().date()
                        kk.management_profile=management                        
                        kk.created_by=rejin.id
                        kk.save()
                        temp_family.outer_invest_amount += kk.investment_amt
                        temp_family.investers_share_count += kk.share_count
                        temp_family.save()
                        ChitFundInterestOverallReport.objects.create(chitfund=temp_family,management_profile=management,amount=kk.investment_amt,
                                                                     income_choice='Investment',created_by=rejin.id,chitinvesters=kk)
                         
                    # temp_family.total_chitfund_amount = (temp_family.outer_invest_amount) + (temp_family.management_amt)  
                    temp_family.cash_inhand_amount = (temp_family.outer_invest_amount) + (temp_family.management_amt)                                          
                    temp_family.total_share_count =(temp_family.management_share_count) + (temp_family.investers_share_count)
                    temp_family.save()
                    # check for inside chit fund cash in hand amount
                    
                        # temp_family.total_chitfund_amount = (temp_family.outer_invest_amount) + (temp_family.management_amt)                        
                        # temp_family.total_share_count =(temp_family.management_share_count) + (temp_family.investers_share_count)
                        # temp_family.save()                 
                return Response(serializer876.data,status=status.HTTP_201_CREATED)
            else:
                return Response(serializer876.errors,status=status.HTTP_400_BAD_REQUEST)
        return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)
        
        #  ChitFundsDetailsSerializer26
    elif request.method == 'GET':
        our_family = ChitFundsDetails.objects.filter(management_profile=management)
        serializer = ChitFundsDetailsSerializer26(our_family,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
        
        

@api_view(['GET','PUT',"DELETE"])
def edit_chit_fund(request,pk):    
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
        
    get_role=rejin.user_role
    if rejin.my_role!=None:
        permiss=Permisions.objects.filter(id=rejin.my_role.id).first()
        if permiss:
            perm=Permisions.objects.get(id=rejin.my_role.id)
            
    try:
        customer = ChitFundsDetails.objects.get(pk=pk,management_profile=management)  
    except ChitFundsDetails.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        # serializer = ChitFundsDetailsSerializer(customer)
        serializer = ChitFundsDetailssSerializer(customer)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    elif request.method == 'PUT':
        if get_role=="User" and perm.chit_fund_edit ==True or get_role=="Admin" or rejin.is_superuser == True: 
            # inter=PeopleInterestDetails.objects.filter(chitt_fund=pk)
            # if inter:
            #     return Response({"Message":"Can't be edited"},status=status.HTTP_226_IM_USED)
            try:
                print('super human')
                print(request.data)
                prod=request.data
                dict87={}
                try:
                    dict87['id']=prod['id']
                except:
                    pass
                dict87['chit_name']=prod['chit_name']
                dict87['starting_date']=prod['starting_date']
                dict87['management_amt']=float(prod['management_amt'])
                dict87['management_share_count']=prod["management_share_count"]
                dict87['fixed_chitfund_amount']=prod["fixed_chitfund_amount"]

                pre_cf_amt=customer.management_amt
                # cash=ManagementTreasure.objects.filter(management_profile=management).first().cash_in_hand
                cash=ManagementTreasure.objects.filter(management_profile=management).first()
                hand_amt=float(cash.cash_in_hand)-float(cash.expence_amt)+float(pre_cf_amt)
                if dict87['management_amt']>hand_amt:
                # if dict87['management_amt']>cash:
                    return Response({"Message":"Entered Amount exceeds the cash in hand amount"},status=status.HTTP_226_IM_USED)
                dict87['set_profit_percent']=prod['set_profit_percent']
                dict87['set_intrest_percent']=prod['set_intrest_percent']
                print('godd')
                print(request.data['field_count'])
                print(type(request.data['field_count']))
                pc=int(request.data['field_count'])
                print(pc)
                print(type(pc))
                produ_list=[]
                if pc>=1:
                    for num in range(1,pc+1):
                        dict8={}
                        try:
                            if prod[f"chit[{num}][id]"]=='null':
                                pass
                            else:
                                p_id=prod[f"chit[{num}][id]"]
                                dict8['id']=p_id
                        except:
                            pass
                        
                        try:
                            if prod[f"chit[{num}][invester_member]"]=='null':
                                pass
                            else:
                                dict8['invester_member']=prod[f"chit[{num}][invester_member]"]
                        except:
                            pass
                        
                        dict8['invester_type']=prod[f"chit[{num}][invester_type]"]
                        dict8['invester_name']=prod[f"chit[{num}][invester_name]"]
                        dict8['invester_address']=prod[f"chit[{num}][invester_address]"]
                        dict8['invester_email']=prod[f"chit[{num}][invester_email]"]
                        dict8['invester_mobile']=prod[f"chit[{num}][invester_mobile]"]
                        dict8['investment_amt']=prod[f"chit[{num}][investment_amt]"]
                        dict8['share_count']=prod[f"chit[{num}][share_count]"]
                        try:
                            dict8['images']=prod[f"chit[{num}][images]"]
                        except:
                            pass
                        try:
                            dict8['documents']=prod[f"chit[{num}][documents]"]
                        except:
                            pass    
                        
                        try:
                            if prod[f"chit[{num}][photo_status]"]=='false':
                                dict8['im_status']=False
                            else:
                                dict8['im_status']=True
                        except:
                            pass
                        
                        try:
                            if prod[f"chit[{num}][doc_status]"]=='false':
                                dict8['doc_status']=False
                            else:
                                dict8['doc_status']=True
                        except:
                            pass
                        
                                            
                        produ_list.append(dict8)        
                dict87['chitt_fund']=produ_list
                print('final')
                print(dict87)
            except:
                return Response({"Message":"Data requirement error"},status=status.HTTP_417_EXPECTATION_FAILED)
                    
            serializer876 = ChitFundsDetailsSerializer(customer,data=dict87)
            if serializer876.is_valid():
                inter=PeopleInterestDetails.objects.filter(chitt_fund=pk)
                if inter:
                    customer.set_profit_percent=float(dict87['set_profit_percent'])
                    customer.set_intrest_percent=float(dict87['set_intrest_percent'])
                    customer.save()
                    return Response({"Message":"Can't be edited This chit amount used.! Only change Profit&Interest percentage."},status=status.HTTP_226_IM_USED)
                tre_cash=ManagementTreasure.objects.filter(management_profile=management).first()
                tre_cash.cash_in_hand += customer.management_amt
                tre_cash.save()
                
                get_investers4=ChitFundInvesters.objects.filter(chitt_fund=customer)
                # get_investers4=ChitFundInvesters.objects.filter(first_investers=True,chitt_fund=customer)
                if get_investers4:
                    for kk in get_investers4:
                        customer.outer_invest_amount -= kk.investment_amt
                        customer.investers_share_count -= kk.share_count
                        customer.save() 
                    # customer.total_chitfund_amount = (customer.outer_invest_amount) + (customer.management_amt)   
                    customer.cash_inhand_amount = (customer.outer_invest_amount) + (customer.management_amt)                                     
                    customer.total_share_count =(customer.management_share_count) + (customer.investers_share_count)
                    customer.save()
                                
                temp_family=serializer876.save()
                temp_family.created_by=rejin.id
                temp_family.management_profile=management
                temp_family.save()
                
                # image and doc
                for im in produ_list:
                    try:
                        print('sts1')
                        u=im['id']
                        if u:
                            try:
                                print('sts2')
                                if im['im_status']==False:
                                    check_object=ChitFundInvesters.objects.filter(id=u).first()
                                    if check_object:
                                        check_object.images=None
                                        check_object.save()
                            except:
                                print('sts2 false')
                                pass
                            
                            try:
                                print('sts2')
                                if im['doc_status']==False:
                                    check_object1=ChitFundInvesters.objects.filter(id=u).first()
                                    if check_object1:
                                        check_object1.documents=None
                                        check_object1.save()
                            except:
                                print('sts2 false')
                                pass
                    except:
                        print('sts1 false')
                        pass
                    continue
                
                cash_in=ManagementTreasure.objects.filter(management_profile=management).first()
                cash_in.cash_in_hand -= temp_family.management_amt
                cash_in.save()
                # pending for create report
                chit_report1=ChitFundInterestOverallReport.objects.filter(chitfund=customer,management_profile=management,managee=True,income_choice='Investment').first()
                if chit_report1:
                    chit_report1.amount=temp_family.management_amt
                    chit_report1.created_by=rejin.id
                    chit_report1.save()
                else:
                    ChitFundInterestOverallReport.objects.create(chitfund=temp_family,management_profile=management,amount=temp_family.management_amt,
                                                             income_choice='Investment',managee=True,created_by=rejin.id)
                treport3=Report.objects.filter(chit_fund=temp_family,management_profile=management,type_choice='Reduction').first()
                if treport3:
                    treport3.amount=temp_family.management_amt
                    treport3.created_by=rejin.id
                    treport3.save()
                else:
                    Report.objects.create(chit_fund=temp_family,management_profile=management,amount=temp_family.management_amt,type_choice='Reduction',created_by=rejin.id)
                  
                # get_investers=ChitFundInvesters.objects.filter(first_investers=True,chitt_fund_id=temp_family.id)
                get_investers=ChitFundInvesters.objects.filter(chitt_fund_id=temp_family.id)
                if get_investers:
                    for kk in get_investers:
                        kk.joining_date=datetime.datetime.today().date()
                        kk.management_profile=management                        
                        kk.created_by=rejin.id
                        kk.save()
                        temp_family.outer_invest_amount += kk.investment_amt
                        temp_family.investers_share_count += kk.share_count
                        temp_family.save()
                        chit_inves_report1=ChitFundInterestOverallReport.objects.filter(chitfund=customer,management_profile=management,income_choice='Investment',chitinvesters=kk).first()
                        if chit_inves_report1:
                            chit_inves_report1.amount=kk.investment_amt
                            chit_inves_report1.created_by=rejin.id
                            chit_inves_report1.save()
                        else:
                            ChitFundInterestOverallReport.objects.create(chitfund=customer,management_profile=management,amount=kk.investment_amt,
                                                                     income_choice='Investment',created_by=rejin.id,chitinvesters=kk)
                    # temp_family.total_chitfund_amount = (temp_family.outer_invest_amount) + (temp_family.management_amt)
                    temp_family.cash_inhand_amount = (temp_family.outer_invest_amount) + (temp_family.management_amt)
                    temp_family.total_share_count =(temp_family.management_share_count) + (temp_family.investers_share_count)
                    temp_family.save()  
                return Response(serializer876.data,status=status.HTTP_201_CREATED)
            else:
                return Response(serializer876.errors,status=status.HTTP_400_BAD_REQUEST)
        return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)
        
                
    elif request.method == 'DELETE':
        if get_role=="User" and perm.chit_fund_delete ==True or get_role=="Admin" or rejin.is_superuser == True or get_role=="User" and perm.chit_fund_edit ==True:
            inter=PeopleInterestDetails.objects.filter(chitt_fund=pk)
            check_settlement= ChitFundSettlement.objects.filter(chitt_fund=customer)
            check_distribution=ChitFundDistribution.objects.filter(chitt_fund=customer)
            if inter or check_settlement or check_distribution:
                return Response({"Message":"Can't be deleted"},status=status.HTTP_226_IM_USED) 
            customer.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)


@api_view(['GET','POST'])
def add_chit_fund_investors(request):
    rejin=token_checking(request)
    if not rejin:
        return Response({"message":"No User Found"},status=status.HTTP_401_UNAUTHORIZED)
    if not rejin.is_active:
        return Response({"message":"Not Authorized Please Contact Admin"},status=status.HTTP_401_UNAUTHORIZED)
    print(f'token---{rejin}')
    
    check_management=ManagementDetails.objects.all()
    if not check_management:
        dict6={}
        dict6['message']= "First Add Management Profile details"
        return Response(dict6,status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        management=ManagementDetails.objects.all().first()
    get_role=rejin.user_role
    if rejin.my_role!=None:
        permiss=Permisions.objects.filter(id=rejin.my_role.id).first()
        if permiss:
            perm=Permisions.objects.get(id=rejin.my_role.id)

    if request.method =='POST': 
        if get_role=="User" and perm.chit_fund_add ==True or get_role=="Admin" or rejin.is_superuser == True: 
            try:
                chit_fund=request.data['chitt_fund']  
            except:
                return Response({"Message":"Data requirement error"},status=status.HTTP_417_EXPECTATION_FAILED)
            
            try:
                customer = ChitFundsDetails.objects.get(pk=request.data['chitt_fund'],management_profile=management)  
            except ChitFundsDetails.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
                
            serializer876 = ChitFundInvestersSerializer2(data=request.data)
            if serializer876.is_valid():
                if customer.action:
                    temp_family=serializer876.save()
                    temp_family.created_by=rejin.id
                    temp_family.management_profile=management
                    temp_family.joining_date=datetime.date.today()
                    temp_family.save()
                    chit_fund=request.data['chitt_fund']
                    chit_amount=ChitFundsDetails.objects.filter(id=chit_fund).first()
                    chit_amount.outer_invest_amount += temp_family.investment_amt 
                    # chit_amount.total_chitfund_amount+=temp_family.investment_amt 
                    chit_amount.cash_inhand_amount+=temp_family.investment_amt 
                    chit_amount.investers_share_count += temp_family.share_count
                    chit_amount.total_share_count +=temp_family.share_count
                    chit_amount.save()
                    ChitFundInterestOverallReport.objects.create(chitfund=customer,management_profile=management,amount=temp_family.investment_amt,
                                                                     income_choice='Investment',created_by=rejin.id,chitinvesters=temp_family)
                    return Response(serializer876.data,status=status.HTTP_201_CREATED)
                else:
                    return Response({'message':"Selected Chit-Fund is not active"},status=status.HTTP_406_NOT_ACCEPTABLE)  
            else:
                return Response(serializer876.errors,status=status.HTTP_400_BAD_REQUEST)
        return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)
    elif request.method == 'GET':
        our_family = ChitFundInvesters.objects.filter(management_profile=management,first_investers=False,action=True)
        serializer = ChitFundInvestersSerializer2(our_family,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
        
        
@api_view(['GET','PUT','PATCH',"DELETE"])
def edit_chit_fund_investors(request,pk):
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
        
    get_role=rejin.user_role
    if rejin.my_role!=None:
        permiss=Permisions.objects.filter(id=rejin.my_role.id).first()
        if permiss:
            perm=Permisions.objects.get(id=rejin.my_role.id)
    try:
        customer = ChitFundInvesters.objects.get(pk=pk)  
        old=customer.investment_amt
        precount=customer.share_count
        # date=customer.created_at__date
        date=customer.created_at.date
    except ChitFundInvesters.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = ChitFundInvestersSerializer2(customer)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    elif request.method == 'PUT':
        if get_role=="User" and perm.chit_fund_edit ==True or get_role=="Admin" or rejin.is_superuser == True: 
            interest_check=PeopleInterestDetails.objects.filter(created_at__date__gte=date)
            check_settlement_apli=ChitFundsettleAplication.objects.filter(investers=customer)
            settlemnt=ChitFundSettlement.objects.filter(investers=customer)
            distri=InvestersProfitDistributionTable.objects.filter(investers=customer)
            if interest_check or check_settlement_apli or settlemnt or distri:
                return Response({"Message":"Cant be edited as the invested amount is used in interest or Other operations involved.!"},status=status.HTTP_300_MULTIPLE_CHOICES)
            try:
                chit_fund=request.data['chitt_fund']  
            except:
                return Response({"Message":"Data requirement error"},status=status.HTTP_417_EXPECTATION_FAILED)
            
            try:
                ChitFundsDetails.objects.get(pk=request.data['chitt_fund'],management_profile=management)  
            except ChitFundsDetails.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
                       
            serializer876 = ChitFundInvestersSerializer2(customer,data=request.data)
            if serializer876.is_valid():
                # revert
                chit_amount1=ChitFundsDetails.objects.filter(id=chit_fund).first()
                chit_amount1.outer_invest_amount -= old 
                # chit_amount1.total_chitfund_amount=(chit_amount1.management_amt) + (chit_amount1.outer_invest_amount)
                chit_amount1.cash_inhand_amount-=old
                chit_amount1.total_share_count-=precount
                chit_amount1.investers_share_count-=precount
                chit_amount1.save() 
                
                temp_family=serializer876.save()
                temp_family.created_by=rejin.id
                temp_family.save()                
                chit_amount=ChitFundsDetails.objects.filter(id=chit_fund).first()
                chit_amount.outer_invest_amount += temp_family.investment_amt 
                chit_amount.cash_inhand_amount+=temp_family.investment_amt 
                # chit_amount.total_chitfund_amount=(chit_amount.management_amt) + (chit_amount.outer_invest_amount)
                chit_amount.investers_share_count += temp_family.share_count
                chit_amount.total_share_count +=temp_family.share_count
                chit_amount.save()
                
                report635=ChitFundInterestOverallReport.objects.filter(chitfund=customer.chitt_fund,management_profile=management,income_choice='Investment',chitinvesters=temp_family).first()
                if report635:
                    report635.amount=temp_family.investment_amt 
                    report635.created_by=rejin.id
                    report635.save()
                else:
                    ChitFundInterestOverallReport.objects.create(chitfund=customer.chitt_fund,management_profile=management,amount=temp_family.investment_amt,
                                                                     income_choice='Investment',created_by=rejin.id,chitinvesters=temp_family)
                return Response(serializer876.data,status=status.HTTP_201_CREATED)
            else:
                return Response(serializer876.errors,status=status.HTTP_400_BAD_REQUEST)
        return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)
    
    # elif request.method == 'PATCH':
    #     if get_role=="User" and perm.chit_fund_edit ==True or get_role=="Admin" or rejin.is_superuser == True:    
    #         serializer876 = ChitFundInvestersSerializer2(customer,data=request.data,partial=True)
    #         if serializer876.is_valid():
    #             temp_family=serializer876.save()
    #             temp_family.created_by=rejin.id
    #             temp_family.save()
    #             return Response(serializer876.data,status=status.HTTP_201_CREATED)
    #         else:
    #             return Response(serializer876.errors,status=status.HTTP_400_BAD_REQUEST)
    #     return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)
            
    elif request.method == 'DELETE':
        if get_role=="User" and perm.chit_fund_edit ==True or get_role=="Admin" or rejin.is_superuser == True or get_role=="User" and perm.chit_fund_delete ==True:
            interest_check=PeopleInterestDetails.objects.filter(created_at__date__gte=date)
            check_settlement_apli=ChitFundsettleAplication.objects.filter(investers=customer)
            settlemnt=ChitFundSettlement.objects.filter(investers=customer)
            distri=InvestersProfitDistributionTable.objects.filter(investers=customer)
            if interest_check or check_settlement_apli or settlemnt or distri:
                return Response({"Message":"Cant be edited as the invested amount is used in interest or Other operations involved.!"},status=status.HTTP_300_MULTIPLE_CHOICES)

            chit_amount1=ChitFundsDetails.objects.filter(id=customer.chitt_fund_id).first()
            if chit_amount1:
                chit_amount1.outer_invest_amount -= old 
                # chit_amount1.total_chitfund_amount-= old
                chit_amount1.cash_inhand_amount-= old
                chit_amount1.investers_share_count -=precount
                chit_amount1.total_share_count -= precount
                chit_amount1.save() 
            customer.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)

@api_view(['GET','POST'])
def add_chit_fund_settlement_application_details(request):
    rejin=token_checking(request)
    if not rejin:
        return Response({"message":"No User Found"},status=status.HTTP_401_UNAUTHORIZED)
    if not rejin.is_active:
        return Response({"message":"Not Authorized Please Contact Admin"},status=status.HTTP_401_UNAUTHORIZED)
    print(f'token---{rejin}')
    
    check_management=ManagementDetails.objects.all()
    if not check_management:
        dict6={}
        dict6['message']= "First Add Management Profile details"
        return Response(dict6,status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        management=ManagementDetails.objects.all().first()
        
    get_role=rejin.user_role
    if rejin.my_role!=None:
        permiss=Permisions.objects.filter(id=rejin.my_role.id).first()
        if permiss:
            perm=Permisions.objects.get(id=rejin.my_role.id)
            
    if request.method =='POST': 
        if get_role=="User" and perm.chit_fund_add ==True or get_role=="Admin" or rejin.is_superuser == True:    
            serializer876 = ChitFundsettleAplicationSerializer(data=request.data)
            if serializer876.is_valid():
                temp_family=serializer876.save()
                temp_family.created_by=rejin.id
                temp_family.management_profile=management
                temp_family.save()
                fund_invest=ChitFundInvesters.objects.filter(chitt_fund=temp_family.chitt_fund,id=temp_family.investers_id).first()
                invest_amount=fund_invest.investment_amt
                
                total_fund_amount_details=ChitFundsDetails.objects.filter(id=temp_family.chitt_fund_id).first()
                # total_fund_amount=total_fund_amount_details.total_chitfund_amount
                total_profit_amount=total_fund_amount_details.profit_amount
                temple_amount1=total_profit_amount * (total_fund_amount_details.set_profit_percent/100)
                temple_amount=round((temple_amount1), 2)
                
                remaining_amount=total_profit_amount-temple_amount
                member_count=total_fund_amount_details.total_share_count
                shared_amount1=remaining_amount/(member_count)
                shared_amount=round((shared_amount1), 2)
                
                invest_fund=ChitFundInvesters.objects.filter(id=temp_family.investers_id).first()
                inve_share_count=invest_fund.share_count
                # invest_fund.share_amount=Decimal(str(float(inve_share_count)*float(shared_amount)))
                invest_fund.share_amount=Decimal(str(invest_fund.collected_share_amount))

                invest_fund.application_date=temp_family.settlement_date
                invest_fund.action=False 
                invest_fund.save() 
                invest_fund.final_settlement_amount =  (invest_fund.investment_amt) + (invest_fund.share_amount)
                invest_fund.save()

                # Once an investor settles out of the chit their shares
                # leave the profit-sharing pool.  We *redistribute* those
                # shares proportionally to the remaining shareholders —
                # both the Management (its baseline share, e.g. 1) and the
                # remaining active investors — so that Management continues
                # to receive its fair slice of future profit collections.
                exit_shares = int(inve_share_count or 0)
                if exit_shares > 0:
                    mgmt_shares = int(total_fund_amount_details.management_share_count or 0)
                    remaining_invs = list(
                        ChitFundInvesters.objects.filter(
                            chitt_fund=total_fund_amount_details,
                            settled=False,
                            action=True,
                        ).exclude(id=invest_fund.id)
                    )
                    remaining_total = sum(int(i.share_count or 0) for i in remaining_invs)
                    denom = mgmt_shares + remaining_total

                    if denom > 0:
                        # Proportional integer split using largest-remainder method
                        allocations = []  # list of (obj, floor_bonus, remainder)

                        mgmt_raw = exit_shares * mgmt_shares / denom
                        mgmt_floor = int(mgmt_raw)
                        allocations.append(("mgmt", None, mgmt_floor, mgmt_raw - mgmt_floor))

                        for inv in remaining_invs:
                            inv_share = int(inv.share_count or 0)
                            raw = exit_shares * inv_share / denom
                            floor_b = int(raw)
                            allocations.append(("inv", inv, floor_b, raw - floor_b))

                        distributed = sum(a[2] for a in allocations)
                        leftover = exit_shares - distributed
                        # Hand out the +1 remainders to those with the largest
                        # fractional part (Management wins ties by design —
                        # it appears first in the list).
                        ordered = sorted(
                            range(len(allocations)), key=lambda k: -allocations[k][3]
                        )
                        for k in ordered[:leftover]:
                            kind, obj, fb, rem = allocations[k]
                            allocations[k] = (kind, obj, fb + 1, rem)

                        # Apply bonuses
                        mgmt_bonus = 0
                        investor_bonus_total = 0
                        for kind, obj, bonus, _ in allocations:
                            if bonus <= 0:
                                continue
                            if kind == "mgmt":
                                mgmt_bonus += bonus
                            else:
                                obj.share_count = int(obj.share_count or 0) + bonus
                                obj.save()
                                investor_bonus_total += bonus

                        total_fund_amount_details.management_share_count = mgmt_shares + mgmt_bonus
                        # Investors lose the exiting shares but gain their proportional bonus
                        total_fund_amount_details.investers_share_count = (
                            int(total_fund_amount_details.investers_share_count or 0)
                            - exit_shares
                            + investor_bonus_total
                        )
                    else:
                        # No remaining pool to share with (edge case) — just
                        # reduce the investor count and leave management alone.
                        total_fund_amount_details.investers_share_count = (
                            int(total_fund_amount_details.investers_share_count or 0)
                            - exit_shares
                        )

                    # Keep total_share_count consistent with its two components
                    total_fund_amount_details.total_share_count = (
                        int(total_fund_amount_details.management_share_count or 0)
                        + int(total_fund_amount_details.investers_share_count or 0)
                    )
                    # Also reduce the invested principal held in the pool
                    total_fund_amount_details.outer_invest_amount = float(
                        total_fund_amount_details.outer_invest_amount or 0
                    ) - float(invest_fund.investment_amt or 0)
                    total_fund_amount_details.save()

                return Response(serializer876.data,status=status.HTTP_201_CREATED)
            else:
                return Response(serializer876.errors,status=status.HTTP_400_BAD_REQUEST)
        return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)
    elif request.method == 'GET':
        our_family = ChitFundsettleAplication.objects.filter(management_profile=management)
        serializer = ChitFundsettleAplicationSerializer(our_family,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
        
        
@api_view(['GET','PUT','PATCH',"DELETE"])
def edit_chit_fund_settlement_application_details(request,pk):
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
    
    get_role=rejin.user_role
    if rejin.my_role!=None:
        permiss=Permisions.objects.filter(id=rejin.my_role.id).first()
        if permiss:
            perm=Permisions.objects.get(id=rejin.my_role.id)
    try:
        customer = ChitFundsettleAplication.objects.get(pk=pk,management_profile=management)  
    except ChitFundsettleAplication.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = ChitFundsettleAplicationSerializer(customer)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    # elif request.method == 'PUT':
    #     if get_role=="User" and perm.chit_fund_edit ==True or get_role=="Admin" or rejin.is_superuser == True:
    #         settlement_check=ChitFundSettlement.objects.filter(chitt_settilement=pk).first()
    #         if settlement_check:
    #             return Response({"Message":"Cant be edited as the amount is settled"},status=status.HTTP_300_MULTIPLE_CHOICES)    
    #         serializer876 = ChitFundsettleAplicationSerializer(customer,data=request.data)
    #         if serializer876.is_valid():
    #             temp_family=serializer876.save()
    #             temp_family.created_by=rejin.id
    #             temp_family.save()
    #             fund_invest=ChitFundInvesters.objects.filter(chitt_fund=temp_family.chitt_fund,id=temp_family.investers_id).first()
    #             invest_amount=fund_invest.investment_amt

    #             total_fund_amount_details=ChitFundsDetails.objects.filter(id=temp_family.chitt_fund_id).first()
    #             total_fund_amount=total_fund_amount_details.total_chitfund_amount
    #             total_profit_amount=total_fund_amount_details.profit_amount
    #             temple_amount=total_profit_amount * (total_fund_amount_details.set_profit_percent/100)
    #             remaining_amount=total_profit_amount-temple_amount


    #             member_count=total_fund_amount_details.total_share_count
    #             shared_amount=remaining_amount/(member_count)
    #             invest_fund=ChitFundInvesters.objects.filter(id=temp_family.investers_id).first()
    #             invest_fund.share_amount=shared_amount
    #             invest_fund.application_date=temp_family.settlement_date
    #             invest_fund.final_settlement_amount =  (invest_fund.investment_amt) + (invest_fund.share_amount)
    #             invest_fund.save()
    #             return Response(serializer876.data,status=status.HTTP_201_CREATED)
    #         else:
    #             return Response(serializer876.errors,status=status.HTTP_400_BAD_REQUEST)
    #     return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)
          
    elif request.method == 'DELETE':
        if get_role=="User" and perm.chit_fund_delete ==True or get_role=="Admin" or rejin.is_superuser == True or get_role=="User" and perm.chit_fund_edit ==True: 
            settlement_check=ChitFundSettlement.objects.filter(chitt_settilement_id=pk)
            if settlement_check:
                return Response({"Message":"Cant be deleted as the amount is settled"},status=status.HTTP_300_MULTIPLE_CHOICES)
            else:
                invest_fund=ChitFundInvesters.objects.filter(id=customer.investers_id).first()
                invest_fund.share_amount=0
                invest_fund.application_date=None
                invest_fund.action=True
                invest_fund.final_settlement_amount=0
                invest_fund.save()
                customer.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)

    
@api_view(['GET'])
def chit_fund_settlement_application_get(request):
    rejin=token_checking(request)
    if not rejin:
        return Response({"message":"No User Found"},status=status.HTTP_401_UNAUTHORIZED)
    if not rejin.is_active:
        return Response({"message":"Not Authorized Please Contact Admin"},status=status.HTTP_401_UNAUTHORIZED)
    print(f'token---{rejin}')
    
    check_management=ManagementDetails.objects.all()
    if not check_management:
        dict6={}
        dict6['message']= "First Add Management Profile details"
        return Response(dict6,status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        management=ManagementDetails.objects.all().first()
    
    get_role=rejin.user_role
    if rejin.my_role!=None:
        permiss=Permisions.objects.filter(id=rejin.my_role.id).first()
        if permiss:
            perm=Permisions.objects.get(id=rejin.my_role.id)

    if request.method == 'GET':
        cal_today=datetime.datetime.now()
        cal_month=cal_today.month
        cal_year=cal_today.year
        first_date = datetime.date(cal_year, cal_month, 1)
        month_ra=calendar.monthrange(cal_year, cal_month)
        req_date=month_ra[1]
        last_date = datetime.date(cal_year, cal_month, req_date)

        # all_chit_fund_aplication=ChitFundsettleAplication.objects.filter(management_profile=management,action=True)
        all_chit_fund_aplication=ChitFundsettleAplication.objects.filter(management_profile=management,action=True).exclude(created_at__date__gte=first_date,created_at__date__lte=last_date)
        set_apli_list=[]
        for chit_fund in all_chit_fund_aplication:
            dict873={}
            seri38=ChitFundsettleAplicationSerializer(chit_fund)
            investers=ChitFundInvesters.objects.filter(id=chit_fund.investers_id).first()
            seri2=ChitFundInvesterssSerializer(investers)
            dict873['application']=seri38.data
            dict873['investers']=seri2.data
            set_apli_list.append(dict873)
            
        return Response(set_apli_list,status=status.HTTP_200_OK)

    
@api_view(['GET','POST'])
def add_chit_fund_settlement(request):
    rejin=token_checking(request) 
    if not rejin:
        return Response({"message":"No User Found"},status=status.HTTP_401_UNAUTHORIZED)
    if not rejin.is_active:
        return Response({"message":"Not Authorized Please Contact Admin"},status=status.HTTP_401_UNAUTHORIZED)   
    print(f'token---{rejin}')
    get_role=rejin.user_role
    if rejin.my_role!=None:
        permiss=Permisions.objects.filter(id=rejin.my_role.id).first()
        if permiss:
            perm=Permisions.objects.get(id=rejin.my_role.id)
    check_management=ManagementDetails.objects.all()
    if not check_management:
        dict6={}
        dict6['message']= "First Add Management Profile details"
        return Response(dict6,status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        management=ManagementDetails.objects.all().first()        
    if request.method =='POST': 
        if get_role=="User" and perm.chit_fund_add ==True or get_role=="Admin" or rejin.is_superuser == True: 
            # pending for check cheet cash-in hand amount
            serializer876 = ChitFundSettlementSerializer(data=request.data)
            if serializer876.is_valid():
                try:
                    getting_cheet=ChitFundsDetails.objects.filter(id=int(request.data['chitt_fund'])).first()
                    getting_invester=ChitFundInvesters.objects.filter(id=int(request.data['investers'])).first()
                    aplication=ChitFundsettleAplication.objects.filter(id=int(request.data['chitt_settilement'])).first()
                except:
                    return Response({"Message":"Data requirement error"},status=status.HTTP_417_EXPECTATION_FAILED)
                    
                if getting_cheet.cash_inhand_amount<getting_invester.final_settlement_amount:
                    return Response({"Message":"Insufficient amount in the selected Chit-fund.!"},status=status.HTTP_226_IM_USED)
                
                temp_family=serializer876.save()
                temp_family.created_by=rejin.id
                temp_family.management_profile=management
                temp_family.save()
                                
                # try:
                #     chit_invest=ChitFundInvesters.objects.filter(id=temp_family.investers_id).first()
                #     chit_invest.action=False
                #     chit_invest.save()
                #     print('yes mann')
                # except:
                #     print('no mann')
                
                funding=ChitFundInvesters.objects.filter(id=temp_family.investers_id).first()               
                intake=ChitFundsDetails.objects.filter(id=temp_family.chitt_fund_id).first()
                intake.invest_retake += funding.investment_amt
                # NOTE: outer_invest_amount reduction is done at the settlement-application step.
                # Do NOT subtract it again here.
                intake.profit_retake+=funding.share_amount
                intake.profit_amount-=funding.share_amount
                rj_cal=funding.investment_amt+funding.share_amount
                intake.cash_inhand_amount-= rj_cal
                # NOTE: share_count reduction & redistribution to (Management + remaining investors)
                # is performed at the settlement-application step
                # (see add_chit_fund_settlement_application_details).  Do NOT reduce again here or
                # counts will drop below zero on the second call.
                intake.retake_investers_share_count+=funding.share_count
                intake.save()
                funding.settled=True
                funding.settlement_date=datetime.date.today()
                funding.retake_share_count=funding.share_count
                funding.save()
                ChitFundInterestOverallReport.objects.create(chitfund=intake,chitinvesters=funding,chitsettlement=temp_family,management_profile=management,amount=funding.final_settlement_amount,income_choice='Distribution')
                # application
                aplication.action=False
                aplication.save()
                return Response(serializer876.data,status=status.HTTP_201_CREATED)
            else:
                return Response(serializer876.errors,status=status.HTTP_400_BAD_REQUEST)
        return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)
    elif request.method == 'GET':
        our_family = ChitFundSettlement.objects.filter(management_profile=management)
        serializer = ChitFundSettlementSerializer(our_family,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
        
        
@api_view(['GET','PUT','PATCH',"DELETE"])
def edit_chit_fund_settlement(request,pk):
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
    
    get_role=rejin.user_role
    if rejin.my_role!=None:
        permiss=Permisions.objects.filter(id=rejin.my_role.id).first()
        if permiss:
            perm=Permisions.objects.get(id=rejin.my_role.id)
    try:
        customer = ChitFundSettlement.objects.get(pk=pk,management_profile=management)  
        # date_check=customer.created_at__date
        date_check=customer.created_at.date
    except ChitFundSettlement.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = ChitFundSettlementSerializer(customer)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    # elif request.method == 'PUT': 
    #     if get_role=="User" and perm.chit_fund_edit ==True or get_role=="Admin" or rejin.is_superuser == True:   
    #         serializer876 = ChitFundSettlementSerializer(customer,data=request.data)
    #         if serializer876.is_valid():
    #             temp_family=serializer876.save()
    #             temp_family.created_by=rejin.id
    #             temp_family.save()
    #             try:
    #                 chit_invest=ChitFundInvesters.objects.filter(id=temp_family.investers_id).first()
    #                 chit_invest.action=False
    #                 chit_invest.save()
    #                 print('yes mann')
    #             except:
    #                 print('no mann')
    #             funding=ChitFundInvesters.objects.filter(id=temp_family.investers_id).first()                
    #             intake=ChitFundsDetails.objects.filter(id=temp_family.chitt_fund_id).first()
    #             intake.invest_retake += funding.investment_amt
    #             intake.outer_invest_amount -= intake.invest_retake
    #             intake.total_chitfund_amount = intake.management_amt + intake.outer_invest_amount
    #             intake.cash_inhand_amount= intake.total_chitfund_amount + intake.profit_amount
    #             intake.save()
    #             funding.settled=True
    #             funding.save()
    #             return Response(serializer876.data,status=status.HTTP_201_CREATED)
    #         else:
    #             return Response(serializer876.errors,status=status.HTTP_400_BAD_REQUEST)
    #     return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)
    
    # elif request.method == 'PATCH':
    #     if get_role=="User" and perm.chit_fund_edit ==True or get_role=="Admin" or rejin.is_superuser == True:    
    #         serializer876 = ChitFundSettlementSerializer(customer,data=request.data,partial=True)
    #         if serializer876.is_valid():
    #             temp_family=serializer876.save()
    #             temp_family.created_by=rejin.id
    #             temp_family.save()
    #             return Response(serializer876.data,status=status.HTTP_201_CREATED)
    #         else:
    #             return Response(serializer876.errors,status=status.HTTP_400_BAD_REQUEST)
    #     return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)
            
    elif request.method == 'DELETE':
        if get_role=="User" and perm.chit_fund_delete ==True or get_role=="Admin" or rejin.is_superuser == True or get_role=="User" and perm.chit_fund_edit ==True: 
            if date.today() == date_check:
                funding=ChitFundInvesters.objects.filter(id=customer.investers_id).first()                
                intake=ChitFundsDetails.objects.filter(id=customer.chitt_fund_id).first()
                intake.invest_retake -= funding.investment_amt
                intake.outer_invest_amount += funding.investment_amt
                intake.profit_retake-=funding.share_amount
                intake.profit_amount+=funding.share_amount
                rj_cal=funding.investment_amt+funding.share_amount
                intake.cash_inhand_amount+= rj_cal
                # intake.cash_inhand_amount+= (float(funding.investment_amt)+float(funding.share_amount))
                intake.retake_investers_share_count-=funding.share_count
                intake.investers_share_count+=funding.share_count
                intake.total_share_count+=funding.share_count
                intake.save()
                funding.settled=False
                funding.settlement_date=None
                funding.save()
                # application
                aplication=ChitFundsettleAplication.objects.filter(id=customer.chitt_settilement_id).first()
                aplication.action=True
                aplication.save()
                
                customer.delete()            
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"Message":"Cant be deleted"},status=status.HTTP_300_MULTIPLE_CHOICES)
        return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)
    

@api_view(['POST'])
def get_chitfund_distribution(request):
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
    if request.method =='POST':
        try:
            chit_fund=request.data['chit_fund']
        except:
            return Response({"Message":"Data requirement error"},status=status.HTTP_417_EXPECTATION_FAILED)
        
        c_ap=ChitFundsettleAplication.objects.filter(chitt_fund_id=chit_fund)
        for b in c_ap:
            settle=ChitFundSettlement.objects.filter(chitt_fund_id=chit_fund,chitt_settilement=b)
            if not settle:
                return Response({"Message":"This chitfund have pending settlement.!"},status=status.HTTP_226_IM_USED)
                  
        interest_people=PeopleInterestDetails.objects.filter(chitt_fund_id=chit_fund,management_profile=management)
        for i in interest_people:
            interest_id=i.id
            check_balance=PeopleInterestBalanceSheet.objects.filter(interest=interest_id,management_profile=management).first()
            balance=check_balance.balance_amt
            if balance!=0 or balance>0:
                return Response({'message':"Interest Balance amount collection pending"},status.HTTP_302_FOUND)
            
        total_fund_amount_details=ChitFundsDetails.objects.filter(id=chit_fund,management_profile=management).first()
        # total_fund_amount=total_fund_amount_details.total_chitfund_amount
        total_profit_amount=total_fund_amount_details.profit_amount
        temple_amount1=total_profit_amount * (total_fund_amount_details.set_profit_percent/100)
        temple_amount=round((temple_amount1), 2)
        remaining_amount=total_profit_amount-temple_amount
        member_count=total_fund_amount_details.total_share_count
        shared_amount1=remaining_amount/(member_count)
        shared_amount=round((shared_amount1), 2)
        dict={}
        # dict['per_head_share']=shared_amount
        dict['outside_amount']=total_fund_amount_details.outer_invest_amount
        dict['management_amt']=total_fund_amount_details.management_amt
        dict['total_amount']=total_fund_amount_details.cash_inhand_amount
        dict['profit_amount']=total_fund_amount_details.profit_amount
        dict['management_share']=total_fund_amount_details.management_amount
        dict['distribution_percent']=total_fund_amount_details.set_profit_percent
        return Response(dict,status=status.HTTP_200_OK)

   
# settlement and close the chitfund
@api_view(['POST','GET'])
def add_chitfund_distribution(request):
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
    
    get_role=rejin.user_role
    if rejin.my_role!=None:
        permiss=Permisions.objects.filter(id=rejin.my_role.id).first()
        if permiss:
            perm=Permisions.objects.get(id=rejin.my_role.id)

    if request.method =='POST':
        if get_role=="User" and perm.chit_fund_add ==True or get_role=="Admin" or rejin.is_superuser == True:     
            serializer876 = ChitFundsDistributionSerializer(data=request.data)
            if serializer876.is_valid():
                temp_family=serializer876.save()
                temp_family.created_by=rejin.id
                temp_family.management_profile=management
                temp_family.distribution_date=datetime.date.today()
                temp_family.profit=False
                temp_family.save()
                
                set2=ChitFundsDetails.objects.filter(id=temp_family.chitt_fund_id).first()
                set2.action=False
                set2.save()
                temp_family.managee_share_count=set2.management_share_count
                temp_family.save()
                invest=ChitFundInvesters.objects.filter(chitt_fund=temp_family.chitt_fund,settled=False,action=True)
                for i in invest:
                    # inveter_share=(float(i.share_count)*float(temp_family.per_head_share_amount))
                    inveter_share = float(i.collected_share_amount)
                    print(inveter_share)
                    i.share_amount=inveter_share
                    i.final_settlement_amount=(inveter_share) + Decimal(i.investment_amt)
                    i.settlement_date=datetime.date.today()
                    i.settled=True
                    i.retake_share_count=i.share_count
                    i.save()
                    
                    # profit table
                    InvestersProfitDistributionTable.objects.create(management_profile=management,chitt_distribution=temp_family,investers=i,share_count=i.share_count,
                                                                    share_amount=inveter_share,profit_amount=inveter_share,created_by=rejin.id)
                    
                    set2.outer_invest_amount-=i.investment_amt
                    set2.invest_retake+=i.investment_amt
                    set2.investers_share_count-=i.share_count
                    set2.retake_investers_share_count+=i.share_count
                    set2.total_share_count-=i.share_count
                    set2.profit_retake+=inveter_share
                    set2.profit_amount-=inveter_share
                    set2.cash_inhand_amount-=i.final_settlement_amount
                    set2.save()
                    ChitFundInterestOverallReport.objects.create(chitfund=set2,chitinvesters=i,chitdistribution=temp_family,management_profile=management,income_choice='Distribution',
                                                             amount=i.final_settlement_amount,created_by=rejin.id)
                    
                set_value=ManagementTreasure.objects.filter(management_profile=management).first()
                set_value.cash_in_hand += temp_family.management_share
                set_value.save()
                set2.profit_amount-=temp_family.management_share
                set2.profit_retake+=temp_family.management_share
                set2.cash_inhand_amount-=temp_family.management_share
                set2.save()
                
                if set2.management_amt>0:
                    man_share_count=set2.management_share_count
                    # amount=(set2.management_amt) + ((temp_family.per_head_share_amount)*man_share_count)
                    # set_value.cash_in_hand += amount
                    # set_value.save()
                    set2.management_amt-=set2.management_amt
                    set2.management_retake+=set2.management_amt
                    # set2.cash_inhand_amount-=set2.management_amt
                    # set2.profit_amount-=((temp_family.per_head_share_amount)*man_share_count)
                    # set2.profit_retake+=((temp_family.per_head_share_amount)*man_share_count)
                    set2.management_share_count-=man_share_count
                    set2.retake_management_share_count+=man_share_count
                    set2.save()
                else:
                    amount=0
                    
                kovil_amt=float(temp_family.management_share)+float(set2.management_amt)
                # report creation pending
                ChitFundInterestOverallReport.objects.create(chitfund=set2,chitdistribution=temp_family,management_profile=management,income_choice='Distribution',
                                                             amount=kovil_amt,created_by=rejin.id)
                
                Report.objects.create(chit_fund=set2,management_profile=management,type_choice='Addition',amount=kovil_amt,created_by=rejin.id)
                
                return Response(serializer876.data,status=status.HTTP_201_CREATED)
            else:
                return Response(serializer876.errors,status=status.HTTP_400_BAD_REQUEST)
        return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)
    
    elif request.method=="GET":
        distribute=ChitFundDistribution.objects.filter(management_profile=management,profit=False)
        # serializer=ChitFundsDistributionSerializer(distribute,many=True)
        serializer=ChitFundsDistributionSerializer98756(distribute,many=True)
        return Response(serializer.data,status=status.HTTP_201_CREATED)

@api_view(['GET',"DELETE"])
def distributed_chit_fund(request,pk):
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
    try:
        customer666 = ChitFundDistribution.objects.get(pk=pk,management_profile=management,profit=False)  
    except ChitFundDistribution.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = ChitFundsDistributionSerializer(customer666)
        return Response(serializer.data,status=status.HTTP_200_OK)
    elif request.method == 'DELETE':
        # check any distribution after profit sharing
        distri=ChitFundDistribution.objects.filter(chitt_fund=customer666.chitt_fund,created_at__gt=customer666.created_at)
        # pending for check after distribution the amount is going to another process
        check_mang_inter=PeopleInterestDetails.objects.filter(management_profile=management,interest_type='Management Interest',created_at__gt=customer666.created_at)
        if distri or check_mang_inter:
            return Response({"message":"After distribution other operations happening in this chitfund"},status=status.HTTP_226_IM_USED)
            # return Response({"message":"After distribution the amount is used from the management"},status=status.HTTP_226_IM_USED)
            
        set2=ChitFundsDetails.objects.filter(id=customer666.chitt_fund_id).first()
        set2.action=True
        set2.save()
        
        invest=ChitFundInvesters.objects.filter(chitt_fund=customer666.chitt_fund,action=True)
        for i in invest:
            set2.outer_invest_amount+=i.investment_amt
            set2.invest_retake-=i.investment_amt
            set2.investers_share_count+=i.share_count
            set2.retake_investers_share_count-=i.share_count
            set2.total_share_count+=i.share_count
            set2.profit_retake-=i.share_amount
            set2.profit_amount+=i.share_amount
            set2.cash_inhand_amount+=i.final_settlement_amount
            set2.save()
            
            i.share_amount=0
            i.final_settlement_amount=0
            i.settlement_date=None
            i.settled=False
            i.retake_share_count=0
            i.save()
            
        set_value=ManagementTreasure.objects.filter(management_profile=management).first()
        set_value.cash_in_hand -= customer666.management_share
        set_value.save()
        set2.profit_amount+=customer666.management_share
        set2.profit_retake-=customer666.management_share
        set2.cash_inhand_amount+=customer666.management_share
        set2.save()
        
        if set2.management_retake>0:
            man_share_count=set2.retake_management_share_count
            amount=(set2.management_retake) + ((customer666.per_head_share_amount)*man_share_count)
            set_value.cash_in_hand -= amount
            set_value.save()
            set2.management_amt+=set2.management_retake
            set2.management_retake-=set2.management_retake
            set2.cash_inhand_amount+=amount
            set2.profit_amount+=((customer666.per_head_share_amount)*man_share_count)
            set2.profit_retake-=((customer666.per_head_share_amount)*man_share_count)
            set2.management_share_count+=man_share_count
            set2.retake_management_share_count-=man_share_count
            set2.save()

        # Report.objects.create(chit_fund=set2,management_profile=management,type_choice='Addition',amount=kovil_amt,created_by=rejin.id)

        take_re353=Report.objects.filter(chit_fund=set2,management_profile=management,type_choice='Addition').last()
        if take_re353:
            take_re353.delete()

        customer666.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
@api_view(['POST'])
def get_chitfund_members(request):
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
    if request.method =='POST':
        try:
            chit_fund=request.data['chit_fund']
            person_type=request.data['person_type']
        except:
            return Response({"Message":"Data requirement error"},status=status.HTTP_417_EXPECTATION_FAILED)
        
        try:
            ChitFundsDetails.objects.get(pk=chit_fund,management_profile=management)  
        except ChitFundsDetails.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        if person_type=="Member":
            funding=ChitFundInvesters.objects.filter(management_profile=management)
            funds=ChitFundsDetails.objects.get(id=chit_fund,management_profile=management)
            total_out=[]
            out=[]
            for i in funding:
                if i.invester_member!=None:
                    member_id=i.invester_member
                    out.append(member_id.id)
            notfunding=Member_Details.objects.exclude(id__in=out)
            for i in notfunding:
                dic={}
                dic['id']=i.id
                dic['member_name']=i.member_name
                dic['member_age']=i.member_age
                dic['member_email']=i.member_email
                dic['member_mobile_number']=i.member_mobile_number
                dic['address']=i.family.address
                dic['invested_amount']=funds.fixed_chitfund_amount
                total_out.append(dic)
            return Response(total_out,status=status.HTTP_201_CREATED)

@api_view(['GET'])
def get_chitfund_members_amount(request):
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
    user_checks=ChitFundInvesters.objects.filter(id=rejin.chit_fund_investor_id,management_profile=management)
    if user_checks:
        # user_check_amount=user_checks.investment_amt
        # chit_fund=user_checks.chitt_fund
        # fund_get=ChitFundsDetails.objects.filter(id=chit_fund).first()
        # fund_amount=fund_get.total_chitfund_amount
        fund_invest=ChitFundInvesters.objects.filter(id=rejin.chit_fund_investor_id,management_profile=management).first()
        seri2=ChitFundInvesterssSerializer(fund_invest)
        if fund_invest.action:
            invest_amount=fund_invest.investment_amt
            total_fund_amount_details=ChitFundsDetails.objects.filter(id=fund_invest.chitt_fund_id,management_profile=management).first()
            # total_fund_amount=total_fund_amount_details.total_chitfund_amount
            total_profit_amount=total_fund_amount_details.profit_amount
            temple_amount1=total_profit_amount * (total_fund_amount_details.set_profit_percent/100)
            temple_amount=round((temple_amount1), 2)
            remaining_amount=total_profit_amount-temple_amount
            member_count=total_fund_amount_details.total_share_count
            print('gladine jjj')
            print(remaining_amount)
            print('gopi')
            print(member_count)
            
            if member_count>0:
                shared_amount1=remaining_amount/(member_count)
                shared_amount=round((shared_amount1), 2)
                inve_share_count=fund_invest.share_count
                get_share_amount=float(inve_share_count)*float(shared_amount)
            else:
                inve_share_count=fund_invest.share_count
                get_share_amount=0

            
            # profit sharing
            pro_share=InvestersProfitDistributionTable.objects.filter(management_profile=management,investers=fund_invest)
            seri=InvestersProfitDistributionTableSerializer987(pro_share,many=True)
            dict={}
            dict['profile']=seri2.data
            dict['share_amount']= fund_invest.collected_share_amount 
            dict['investment_amount']=invest_amount
            dict['share_count']=inve_share_count
            dict['joining_date']=fund_invest.joining_date
            dict['sharing']=seri.data
            return Response(dict,status=status.HTTP_201_CREATED)
        else:
            # profit sharing
            pro_share=InvestersProfitDistributionTable.objects.filter(management_profile=management,investers=fund_invest)
            seri=InvestersProfitDistributionTableSerializer987(pro_share,many=True)
            dict={}
            dict['profile']=seri2.data
            dict['share_amount']= fund_invest.share_amount
            dict['investment_amount']=fund_invest.investment_amt
            dict['share_count']=fund_invest.share_count
            dict['joining_date']=fund_invest.joining_date
            dict['sharing']=seri.data
            return Response(dict,status=status.HTTP_201_CREATED)


# profit only sharing operation pending
@api_view(['POST','GET'])
def chitfund_only_profit_distribution(request):
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
    
    get_role=rejin.user_role
    if rejin.my_role!=None:
        permiss=Permisions.objects.filter(id=rejin.my_role.id).first()
        if permiss:
            perm=Permisions.objects.get(id=rejin.my_role.id)

    if request.method =='POST':
        if get_role=="User" and perm.chit_fund_add ==True or get_role=="Admin" or rejin.is_superuser == True:     
            serializer876 = ChitFundsDistributionSerializer(data=request.data)
            if serializer876.is_valid():
                temp_family=serializer876.save()
                temp_family.created_by=rejin.id
                temp_family.management_profile=management
                temp_family.distribution_date=datetime.date.today()
                temp_family.profit=True
                temp_family.save()
                
                set2=ChitFundsDetails.objects.filter(id=temp_family.chitt_fund_id).first()
                # set2.action=False
                # set2.save()
                temp_family.managee_share_count=set2.management_share_count
                temp_family.save()
                
                invest=ChitFundInvesters.objects.filter(chitt_fund=temp_family.chitt_fund,settled=False,action=True)
                for i in invest:
                    # inveter_share=(float(i.share_count)*float(temp_family.per_head_share_amount))
                    # inveter_share = Decimal(str(float(i.share_count) * float(temp_family.per_head_share_amount)))
                    inveter_share = i.collected_share_amount

                    
                    # i.share_amount=inveter_share
                    # i.final_settlement_amount=(inveter_share) + (i.investment_amt)
                    # i.settlement_date=datetime.date.today()
                    # i.settled=True
                    # i.retake_share_count=i.share_count
                    # i.save()
                    
                    # profit table
                    InvestersProfitDistributionTable.objects.create(management_profile=management,chitt_distribution=temp_family,investers=i,share_count=i.share_count,
                                                                    share_amount=inveter_share,profit_amount=inveter_share,created_by=rejin.id)
                    
                    # set2.outer_invest_amount-=i.investment_amt
                    # set2.invest_retake+=i.investment_amt
                    # set2.investers_share_count-=i.share_count
                    # set2.retake_investers_share_count+=i.share_count
                    # set2.total_share_count-=i.share_count
                    set2.profit_retake+=inveter_share
                    set2.profit_amount-=inveter_share
                    set2.cash_inhand_amount-=inveter_share
                    set2.save()
                    ChitFundInterestOverallReport.objects.create(chitfund=set2,chitinvesters=i,chitdistribution=temp_family,management_profile=management,income_choice='Distribution',
                                                             amount=i.final_settlement_amount,created_by=rejin.id)
                    
                set_value=ManagementTreasure.objects.filter(management_profile=management).first()
                set_value.cash_in_hand += temp_family.management_share
                set_value.save()
                
                set2.profit_amount-=temp_family.management_share
                set2.profit_retake+=temp_family.management_share
                set2.cash_inhand_amount-=temp_family.management_share
                set2.save()
                
                # manage share 
                # if set2.management_amt>0:
                #     man_share_count=set2.management_share_count
                #     # amount=(set2.management_amt) + ((temp_family.per_head_share_amount)*man_share_count)
                #     # set_value.cash_in_hand += amount
                #     # set_value.save()
                    
                #     # set2.cash_inhand_amount-=amount
                #     # set2.profit_amount-=((temp_family.per_head_share_amount)*man_share_count)
                #     # set2.profit_retake+=((temp_family.per_head_share_amount)*man_share_count)
                #     set2.save()
                # else:
                #     amount=0
                    
                kovil_amt=float(temp_family.management_share)+float(set2.management_amt)
                # report creation pending
                ChitFundInterestOverallReport.objects.create(chitfund=set2,chitdistribution=temp_family,management_profile=management,income_choice='Distribution',
                                                             amount=kovil_amt,created_by=rejin.id)
                
                Report.objects.create(chit_fund=set2,management_profile=management,type_choice='Addition',amount=kovil_amt,created_by=rejin.id)
                
                return Response(serializer876.data,status=status.HTTP_201_CREATED)
            else:
                return Response(serializer876.errors,status=status.HTTP_400_BAD_REQUEST)
        return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)
    
    elif request.method=="GET":
        distribute=ChitFundDistribution.objects.filter(management_profile=management,profit=True)
        serializer=ChitFundsDistributionSerializer98756(distribute,many=True)
        return Response(serializer.data,status=status.HTTP_201_CREATED)
    
@api_view(['GET',"DELETE"])
def profit_only_chit_fund_edit(request,pk):
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
    try:
        customer666 = ChitFundDistribution.objects.get(pk=pk,management_profile=management,profit=True)  
    except ChitFundDistribution.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = ChitFundsDistributionSerializer98756(customer666)
        return Response(serializer.data,status=status.HTTP_200_OK)
    elif request.method == 'DELETE':
        # check any distribution after profit sharing
        distri=ChitFundDistribution.objects.filter(chitt_fund=customer666.chitt_fund,created_at__gt=customer666.created_at)
        # pending for check after distribution the amount is going to another process
        check_mang_inter=PeopleInterestDetails.objects.filter(management_profile=management,interest_type='Management Interest',created_at__gt=customer666.created_at)
        if distri or check_mang_inter:
            return Response({"message":"After distribution other operations happening in this chitfund"},status=status.HTTP_226_IM_USED)
            # return Response({"message":"After distribution the amount is used from the management"},status=status.HTTP_226_IM_USED)
        
        set2=ChitFundsDetails.objects.filter(id=customer666.chitt_fund_id).first()
        
        all_invest=InvestersProfitDistributionTable.objects.filter(chitt_distribution=customer666)
        for inves in all_invest:
            set2.profit_retake-=inves.profit_amount
            set2.profit_amount+=inves.profit_amount
            set2.cash_inhand_amount+=inves.profit_amount
            set2.save()
                
        set_value=ManagementTreasure.objects.filter(management_profile=management).first()
        set_value.cash_in_hand -= customer666.management_share
        set_value.save()
        set2.profit_amount+=customer666.management_share
        set2.profit_retake-=customer666.management_share
        set2.cash_inhand_amount+=customer666.management_share
        set2.save()
        
        if set2.management_amt>0:
            man_share_count=set2.management_share_count
            amount=(set2.management_amt) + ((customer666.per_head_share_amount)*man_share_count)
            set_value.cash_in_hand -= amount
            set_value.save()
            
            set2.cash_inhand_amount+=amount
            set2.profit_amount+=((customer666.per_head_share_amount)*man_share_count)
            set2.profit_retake-=((customer666.per_head_share_amount)*man_share_count)
            set2.save()
            
        take_re353=Report.objects.filter(chit_fund=set2,management_profile=management,type_choice='Addition').last()
        if take_re353:
            take_re353.delete()

        customer666.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    


# registered investers list 
@api_view(['GET'])
def chit_fund_investers_register_list(request):
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
        investerss=User.objects.filter(management_profile=management,user_role='Invester')
        # investerss=User.objects.filter(management_profile=management,chit_fund__isnull=True,chit_fund_investor__isnull=True)
        serializer = RejinUserSerializer78(investerss,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
