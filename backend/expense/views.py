from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from.serializers import ADDExpenseCategorySerializer,ADDExpenseNamesSerializer,ADDExpenseDetailsSerializer
from .models import ADDExpenseCategory,ADDExpenseNames,ADDExpenseDetails
from token_app.views import *
from management.models import ManagementDetails
from permisions.models import Permisions
from treasure.models import ManagementTreasure
from reports.models import Report
from management.models import BankDetails
from datetime import datetime

@api_view(['GET','POST'])
def add_expen_categry(request):
    rejin=token_checking(request)
    if not rejin:
        return Response({"message":"No User Found"},status=status.HTTP_401_UNAUTHORIZED)
    if not rejin.is_active:
        return Response({"message":"Not Authorized Please Contact Admin"},status=status.HTTP_401_UNAUTHORIZED)
    print(f'token---{rejin}')
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
        if get_role=="User" and perm.expense_add ==True or get_role=="Admin" or rejin.is_superuser == True:  
            category_name=request.data['category_name']   
            category_check=ADDExpenseCategory.objects.filter(management_profile=management,category_name=category_name)
            if category_check:
                return Response({'message': 'Similar category name already exists'},status=status.HTTP_302_FOUND)
            serializer876 = ADDExpenseCategorySerializer(data=request.data)
            if serializer876.is_valid():
                temp_family=serializer876.save()
                temp_family.created_by=rejin.id
                temp_family.management_profile=management
                temp_family.save()
                return Response(serializer876.data,status=status.HTTP_201_CREATED)
            else:
                return Response(serializer876.errors,status=status.HTTP_400_BAD_REQUEST)
        return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)
    elif request.method == 'GET':
        our_family = ADDExpenseCategory.objects.filter(management_profile=management)
        serializer = ADDExpenseCategorySerializer(our_family,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
        
        
@api_view(['GET','PUT','PATCH',"DELETE"])
def edit_expen_categry(request,pk):
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
        customer = ADDExpenseCategory.objects.get(pk=pk)  
    except ADDExpenseCategory.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    check_management=ManagementDetails.objects.all()
    if not check_management:
        dict6={}
        dict6['message']= "First Add Management Profile details"
        return Response(dict6,status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        management=ManagementDetails.objects.all().first()
    
    if request.method == 'GET':
        serializer = ADDExpenseCategorySerializer(customer)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    elif request.method == 'PUT':  
        if get_role=="User" and perm.expense_edit ==True or get_role=="Admin" or rejin.is_superuser == True:
            category_check=ADDExpenseDetails.objects.filter(category=pk)
            if category_check:
                return Response({'message': 'Cannot be edited as it is added in expense details'},status=status.HTTP_302_FOUND) 
            category_name=request.data['category_name']
            category_check=ADDExpenseCategory.objects.filter(management_profile=management,category_name=category_name).exclude(id=pk)
            if category_check:
                return Response({'message': 'Similar category namae already exists'},status=status.HTTP_302_FOUND)
            serializer876 = ADDExpenseCategorySerializer(customer,data=request.data)
            if serializer876.is_valid():
                temp_family=serializer876.save()
                temp_family.created_by=rejin.id
                temp_family.management_profile=management
                temp_family.save()
                return Response(serializer876.data,status=status.HTTP_201_CREATED)
            else:
                return Response(serializer876.errors,status=status.HTTP_400_BAD_REQUEST)
        return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)
    
    elif request.method == 'PATCH': 
        if get_role=="User" and perm.expense_edit ==True or get_role=="Admin" or rejin.is_superuser == True:  
            serializer876 = ADDExpenseCategorySerializer(customer,data=request.data,partial=True)
            if serializer876.is_valid():
                temp_family=serializer876.save()
                temp_family.created_by=rejin.id
                temp_family.management_profile=management
                temp_family.save()
                return Response(serializer876.data,status=status.HTTP_201_CREATED)
            else:
                return Response(serializer876.errors,status=status.HTTP_400_BAD_REQUEST)
        return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)
            
    elif request.method == 'DELETE':
        if get_role=="User" and perm.expense_edit ==True or get_role=="Admin" or rejin.is_superuser == True or get_role=="User" and perm.expense_delete ==True:
            category_check=ADDExpenseDetails.objects.filter(category=pk)
            if category_check:
                return Response({'message': 'Cannot be deleted as it is added in expense details'},status=status.HTTP_302_FOUND)
            customer.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)
    
    
@api_view(['GET','POST'])
def add_expen_names(request):
    rejin=token_checking(request)
    if not rejin:
        return Response({"message":"No User Found"},status=status.HTTP_401_UNAUTHORIZED)
    if not rejin.is_active:
        return Response({"message":"Not Authorized Please Contact Admin"},status=status.HTTP_401_UNAUTHORIZED)
    print(f'token---{rejin}')
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
        if get_role=="User" and perm.expense_add ==True or get_role=="Admin" or rejin.is_superuser == True:  
            expense_name=request.data['expense_name']
            expense_check=ADDExpenseNames.objects.filter(management_profile=management,expense_name=expense_name)
            if expense_check:
                return Response({'message': 'Similar expense namae already exists'},status=status.HTTP_302_FOUND)  
            serializer876 = ADDExpenseNamesSerializer(data=request.data)
            if serializer876.is_valid():
                temp_family=serializer876.save()
                temp_family.created_by=rejin.id
                temp_family.management_profile=management                
                temp_family.save()
                return Response(serializer876.data,status=status.HTTP_201_CREATED)
            else:
                return Response(serializer876.errors,status=status.HTTP_400_BAD_REQUEST)
        return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)
    elif request.method == 'GET':
        our_family = ADDExpenseNames.objects.filter(management_profile=management)
        serializer = ADDExpenseNamesSerializer(our_family,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
        
        
@api_view(['GET','PUT','PATCH',"DELETE"])
def edit_expen_names(request,pk):
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
        customer = ADDExpenseNames.objects.get(pk=pk)  
    except ADDExpenseNames.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    check_management=ManagementDetails.objects.all()
    if not check_management:
        dict6={}
        dict6['message']= "First Add Management Profile details"
        return Response(dict6,status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        management=ManagementDetails.objects.all().first()
    
    if request.method == 'GET':
        serializer = ADDExpenseNamesSerializer(customer)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    elif request.method == 'PUT':
        if get_role=="User" and perm.expense_edit ==True or get_role=="Admin" or rejin.is_superuser == True:   
            category_check=ADDExpenseDetails.objects.filter(expense=pk)
            if category_check:
                return Response({'message': 'Cannot be edited as it is added in expense details'},status=status.HTTP_302_FOUND) 
            expense_name=request.data['expense_name']
            expense_check=ADDExpenseNames.objects.filter(management_profile=management,expense_name=expense_name).exclude(id=pk)
            if expense_check:
                return Response({'message': 'Similar expense namae already exists'},status=status.HTTP_302_FOUND)
            serializer876 = ADDExpenseNamesSerializer(customer,data=request.data)
            if serializer876.is_valid():
                temp_family=serializer876.save()
                temp_family.created_by=rejin.id
                temp_family.management_profile=management
                temp_family.save()
                return Response(serializer876.data,status=status.HTTP_201_CREATED)
            else:
                return Response(serializer876.errors,status=status.HTTP_400_BAD_REQUEST)
        return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)
    
    elif request.method == 'PATCH': 
        if get_role=="User" and perm.expense_edit ==True or get_role=="Admin" or rejin.is_superuser == True:  
            serializer876 = ADDExpenseNamesSerializer(customer,data=request.data,partial=True)
            if serializer876.is_valid():
                temp_family=serializer876.save()
                temp_family.created_by=rejin.id
                temp_family.management_profile=management
                temp_family.save()
                return Response(serializer876.data,status=status.HTTP_201_CREATED)
            else:
                return Response(serializer876.errors,status=status.HTTP_400_BAD_REQUEST)
        return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)
            
    elif request.method == 'DELETE':
        if get_role=="User" and perm.expense_delete ==True or get_role=="Admin" or rejin.is_superuser == True or get_role=="User" and perm.expense_edit ==True :
            category_check=ADDExpenseDetails.objects.filter(expense=pk)
            if category_check:
                return Response({'message': 'Cannot be deleted as it is added in expense details'},status=status.HTTP_302_FOUND) 
            customer.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)
    
@api_view(['GET','POST'])
def add_expen_details(request):
    rejin=token_checking(request)
    if not rejin:
        return Response({"message":"No User Found"},status=status.HTTP_401_UNAUTHORIZED)
    if not rejin.is_active:
        return Response({"message":"Not Authorized Please Contact Admin"},status=status.HTTP_401_UNAUTHORIZED)
    print(f'token---{rejin}')
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
        if get_role=="User" and perm.expense_add ==True or get_role=="Admin" or rejin.is_superuser == True:     
            serializer876 = ADDExpenseDetailsSerializer(data=request.data)
            if serializer876.is_valid():
                print(request.data)
                try:
                    bank=request.data['bank']
                except:
                    pass
                expense_amt=request.data['expense_amt']
                manage=ManagementTreasure.objects.filter(management_profile=management)
                if manage:
                    manage_get=ManagementTreasure.objects.filter(management_profile=management).first()
                    try:
                        if bank != None:
                            bank_check=BankDetails.objects.filter(id=bank).first()
                            if bank_check.credit_amt >= float(expense_amt):                        
                                manage_get.bank_amt =float(manage_get.bank_amt) - float(expense_amt)
                                # manage_get.bank_withdraw_amt=float(manage_get.bank_withdraw_amt) + float(expense_amt)
                                manage_get.save()
                                bank=BankDetails.objects.filter(id=bank).first()
                                bank.debit_amt = float(bank.debit_amt) + float(expense_amt)
                                bank.credit_amt = float(bank.credit_amt) - float(expense_amt)
                                bank.save()
                                manage_get.reduce_expence_amt = float(manage_get.reduce_expence_amt) + float(expense_amt)
                                manage_get.save()
                            else:
                                return Response({'message':"Insufficient bank amount, Only " + f'{int(bank_check.credit_amt)}' + " rupees is available in selected bank"},status.HTTP_302_FOUND) 

                    except:
                            # print("jjjjjjjjjjjjjjjjjjj")
                            # if manage_get.cash_in_hand >= float(expense_amt):
                            #     manage_get.cash_in_hand =float(manage_get.cash_in_hand) - float(expense_amt)
                            #     manage_get.save()
                                manage_get.expence_amt = float(manage_get.expence_amt) + float(expense_amt)
                                manage_get.save()
                            # else:
                    
                            #     return Response({'message':"Insufficient cash amount, Only " + f'{int(manage_get.cash_in_hand)}' + " rupees is available in treasure cashinhand"},status.HTTP_302_FOUND) 
                    
                temp_family=serializer876.save()
                temp_family.created_by=rejin.id
                temp_family.management_profile=management
                temp_family.save()
                
                Report.objects.create(banks=temp_family.bank,type_choice="Reduction",management_profile=temp_family.management_profile,expenses=temp_family,amount=temp_family.expense_amt,created_by=rejin.id)                
                return Response(serializer876.data,status=status.HTTP_201_CREATED)
            else:
                return Response(serializer876.errors,status=status.HTTP_400_BAD_REQUEST)
        return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)
    elif request.method == 'GET':
        our_family = ADDExpenseDetails.objects.filter(management_profile=management)
        serializer = ADDExpenseDetailsSerializer(our_family,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
        
        
@api_view(['GET','PUT','PATCH',"DELETE"])
def edit_expen_details(request,pk):
    rejin=token_checking(request)
    check_management=ManagementDetails.objects.all()
    if not check_management:
        dict6={}
        dict6['message']= "First Add Management Profile details"
        return Response(dict6,status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        management=ManagementDetails.objects.all().first()
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
        customer = ADDExpenseDetails.objects.get(pk=pk)  
        amount_check=customer.expense_amt
        bank_check_get=customer.bank

    except ADDExpenseDetails.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = ADDExpenseDetailsSerializer(customer)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    elif request.method == 'PUT':
        if get_role=="User" and perm.expense_edit ==True or get_role=="Admin" or rejin.is_superuser == True: 
            date_check=  (customer.date.month != datetime.now().month and customer.date.year != datetime.now().year)  or  (customer.date.month != datetime.now().month and customer.date.year == datetime.now().year)   or (customer.date.month == datetime.now().month and customer.date.year != datetime.now().year)     
            if date_check:
                return Response({'message':"Cannot be edited"},status.HTTP_302_FOUND)   
            serializer876 = ADDExpenseDetailsSerializer(customer,data=request.data)
            if serializer876.is_valid():
                if customer.payment_mode == "Online":
                    customer.bank=None
                    customer.transaction_no=None
                    customer.transaction_date=None
                    customer.transaction_type=None
                    customer.bank_name=None
                    customer.bank_pay=None
                    customer.save()
                elif customer.payment_mode == "Offline":
                    if customer.transaction_type == "Cheque":
                        customer.transaction_no=None
                        customer.transaction_date=None
                        customer.cheque_no =None
                        customer.save()
                manage=ManagementTreasure.objects.filter(management_profile=management)
                if manage:
                    manage_get=ManagementTreasure.objects.filter(management_profile=management).first()
                    if bank_check_get != None:                 
                        
                            manage_get.bank_amt =float(manage_get.bank_amt) + float(amount_check)                            
                            bank_previous=BankDetails.objects.filter(id=bank_check.id).first()
                            bank_previous.debit_amt = float(bank.debit_amt) -  float(amount_check)
                            bank_previous.credit_amt = float(bank.credit_amt) + float(amount_check)
                            # bank.save()                                           

                    else:
                                               
                        manage_get.expence_amt = float(manage_get.expence_amt) - float(amount_check)
                        # manage_get.save()
                       
                print(request.data)
                try:
                    bank=request.data['bank']
                except:
                    pass
                expense_amt=request.data['expense_amt']
                
                manage1=ManagementTreasure.objects.filter(management_profile=management)
                if manage1:
                    manage_get1=ManagementTreasure.objects.filter(management_profile=management).first()
                    try:
                        if bank != None:

                            bank_check=BankDetails.objects.filter(id=bank).first()
                            if bank_check.credit_amt >= float(expense_amt): 
                                manage_get1.bank_amt =float(manage_get1.bank_amt) - float(expense_amt)
                                # manage_get1.bank_withdraw_amt=float(manage_get1.bank_withdraw_amt) + float(expense_amt)
                                manage_get1.save()
                                bank1=BankDetails.objects.filter(id=bank).first()
                                bank1.debit_amt = float(bank1.debit_amt) +  float(expense_amt)
                                bank1.credit_amt = float(bank1.credit_amt) - float(expense_amt)
                                bank1.save()                               
                                manage_get.save()
                                print("tttttttttttttttt")
                                print(bank_check)
                                if bank_check_get != None:
                                    print(bank_previous)

                                    bank_previous.save()                                                  

                            else:
                                return Response({'message':"Insufficient bank amount, Only " + f'{int(bank_check.credit_amt)}' + " rupees is available in selected bank"},status.HTTP_302_FOUND) 
                    except:
                            
                            # if manage_get1.cash_in_hand >= float(expense_amt):
                            #     manage_get1.cash_in_hand =float(manage_get1.cash_in_hand) - float(expense_amt)
                            #     manage_get1.save()
                                manage_get1.expence_amt = float(manage_get1.expence_amt) + float(expense_amt)
                                manage_get1.save()
                                manage_get.save()
                                if bank_check_get != None:
                                    bank_previous.save()

                                
                            # else:
                            #     return Response({'message':"Insufficient cash amount, Only " + f'{int(manage_get.cash_in_hand)}' + " rupees is available in treasure cashinhand"},status.HTTP_302_FOUND) 
                   
                temp_family=serializer876.save()
                temp_family.created_by=rejin.id
                temp_family.management_profile=management
                temp_family.save()
                report_check=Report.objects.filter(expenses=pk)
                if report_check:
                    report_checks=Report.objects.filter(expenses=pk).first()
                    report_checks.amount=temp_family.expense_amt
                    report_checks.expenses_id=pk
                    report_checks.banks=temp_family.bank
                    report_checks.management_profile=temp_family.management_profile
                    report_checks.type_choice="Reduction"
                    report_checks.created_by=rejin.id
                    report_checks.save()
                return Response(serializer876.data,status=status.HTTP_201_CREATED)
            else:
                return Response(serializer876.errors,status=status.HTTP_400_BAD_REQUEST)
        return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)
    
    elif request.method == 'PATCH': 
        if get_role=="User" and perm.expense_edit ==True or get_role=="Admin" or rejin.is_superuser == True:  
            serializer876 = ADDExpenseDetailsSerializer(customer,data=request.data,partial=True)
            if serializer876.is_valid():
                temp_family=serializer876.save()
                temp_family.created_by=rejin.id
                temp_family.management_profile=management
                temp_family.save()
                manage=ManagementTreasure.objects.filter(management_profile=management)
                if manage:
                    manage_get=ManagementTreasure.objects.filter(management_profile=management).first()
                    # manage_get.expence_amt = float(manage_get.expence_amt) + float(temp_family.expense_amt) - float(amount)
                    manage_get.save()
                return Response(serializer876.data,status=status.HTTP_201_CREATED)
            else:
                return Response(serializer876.errors,status=status.HTTP_400_BAD_REQUEST)
        return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)
            
    elif request.method == 'DELETE':
        if get_role=="User" and perm.expense_edit ==True or get_role=="Admin" or rejin.is_superuser == True or get_role=="User" and perm.expense_delete ==True:
            date_check=  (customer.date.month != datetime.now().month and customer.date.year != datetime.now().year)  or  (customer.date.month != datetime.now().month and customer.date.year == datetime.now().year)   or (customer.date.month == datetime.now().month and customer.date.year != datetime.now().year)     
            if date_check:
                return Response({'message':"Cannot be deleted"},status.HTTP_302_FOUND) 
            manage1=ManagementTreasure.objects.filter(management_profile=management)
            if manage1:
                manage_get=ManagementTreasure.objects.filter(management_profile=management).first()
                if customer.bank != None:
                    manage_get.bank_amt =float(manage_get.bank_amt) + float(amount_check)
                    # manage_get.bank_withdraw_amt=float(manage_get.bank_withdraw_amt) - float(amount_check)
                    manage_get.reduce_expence_amt = float(manage_get.reduce_expence_amt) - float(amount_check)
                    manage_get.save()
                    bank=BankDetails.objects.filter(id=customer.bank.id).first()
                    bank.debit_amt = float(bank.debit_amt) - float(amount_check)
                    bank.credit_amt = float(bank.credit_amt) + float(amount_check)
                    bank.save()
                else:
                    # manage_get.cash_in_hand =float(manage_get.cash_in_hand) + float(amount_check)
                    # manage_get.save()
                    manage_get.expence_amt = float(manage_get.expence_amt) - float(amount_check)
                    manage_get.save()
            customer.delete()
            report_check=Report.objects.filter(expenses=pk)
            if report_check:
                report_checks=Report.objects.filter(expenses=pk).first()
                report_checks.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'message':"un-authenticate"},status.HTTP_401_UNAUTHORIZED)
    



@api_view(['GET','POST'])
def expense_detail_filter(request):
    rejin=token_checking(request)
    if not rejin:
        return Response({"message":"No User Found"},status=status.HTTP_401_UNAUTHORIZED)
    if not rejin.is_active:
        return Response({"message":"Not Authorized Please Contact Admin"},status=status.HTTP_401_UNAUTHORIZED)
    print(f'token---{rejin}')
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
    
    if request.method == 'POST':
        jj=request.data['range']
        end_date=jj['end_date']
        start_date=jj['start_date']
        if start_date and end_date:
            start_date_time_obj = datetime.strptime(str(start_date), '%Y-%m-%d').date()
            end_date_time_obj = datetime.strptime(str(end_date), '%Y-%m-%d').date()
            our_family = ADDExpenseDetails.objects.filter(management_profile=management,date__gte=start_date_time_obj,date__lte=end_date_time_obj)
            serializer = ADDExpenseDetailsSerializer(our_family,many=True)
            return Response(serializer.data,status=status.HTTP_200_OK)
            