from rest_framework import serializers
from .models import PeopleInterestDetails
from rest_framework.exceptions import ValidationError
from django.utils import timezone
import datetime
from balancesheet.models import PeopleInterestBalanceSheet
from dateutil.relativedelta import *
from datetime import date
from collection.models import CollectionDetails
from datetime import date,timedelta




def interest_no():
    l=PeopleInterestDetails.objects.last()
    if l:
        l=l.id   
    else:
        l=0      
    l=l+1

    return ("INT" '%01d' % l)

class PeopleInterestDetailsSerializer(serializers.ModelSerializer):
    id=serializers.IntegerField(required=False)
    photo=serializers.ImageField(required=False)
    action = serializers.BooleanField(default=True)
    class Meta:
        model =PeopleInterestDetails
        fields = '__all__'
        
    def create(self, validated_data):
        profile_instance = PeopleInterestDetails.objects.create(intrest_no=interest_no(),**validated_data)               
        return profile_instance
    
    
    def validate(self, validated_data): 
            print(validated_data)       
        # if validated_data['interest_type']=="Chit fund Interest":
            if validated_data['interest_date'] > timezone.now().date():
                raise serializers.ValidationError("Interest date cannot be greater than today") 
            else:                
                current_date = datetime.date.today()
                checking_date=validated_data['interest_date']
                print(checking_date)
                print(checking_date.year)
                print(checking_date.month)
                print(current_date.month - 1)

                if checking_date.year == current_date.year and checking_date.month == current_date.month - 1 or checking_date.year == current_date.year and checking_date.month == current_date.month:
                    print("ccccccccccccccccc")
                    return validated_data
                else:
                    raise serializers.ValidationError("Interest can only be added with the interest date of current month and previous month.")


class PeopleInterestBalanceDetailsSerializer(serializers.ModelSerializer):
    id=serializers.IntegerField(required=False)
    # photo=serializers.ImageField(required=False)
    # action = serializers.BooleanField(default=True)
    amount = serializers.SerializerMethodField()
    class Meta:
        model =PeopleInterestDetails
        fields = ['id','management_profile','intrest_no','interest_category','interest_type','chitt_fund',
                        'chit_name','photo','people_type','people_member','people_name','people_address','people_email','people_mobile','principal_amt','interest_amt','interest_period','interest_period_type','installment_amt','amount']
    
    def get_amount(self, obj):
        # Retrieve the related PeopleInterestbalansesheet object
        if obj.interest_category == "Interest":
            interest_balance_sheet = PeopleInterestBalanceSheet.objects.filter(interest=obj).first()
            if interest_balance_sheet:
                print(interest_balance_sheet.intrest_balance_amt)
                print(obj.interest_amt)
                # Calculate the difference between interest_balance and interest_amt
                return interest_balance_sheet.intrest_balance_amt - obj.interest_amt
            return None
        elif obj.interest_category ==  "Installment Interest":
            interest_balance_sheet = PeopleInterestBalanceSheet.objects.filter(interest=obj).first()
            if interest_balance_sheet:
                print(obj)
                print(obj.interest_date)
                print(obj.paid_counts)
                # print(((interest_balance_sheet.interest_apply_date + relativedelta(obj.paid_counts)).month))
                print((datetime.date.today().month))
                print(((datetime.date.today()).day))
                
                if interest_balance_sheet.interest.interest_period_type=="Days":
                    print(((obj.interest_date + relativedelta(days=obj.paid_counts)).day) )
                    terminating_date=(obj.interest_date + relativedelta(days=obj.interest_period))
                    # date1 = datetime.strptime(date_str1, '%Y-%m-%d')
                    
                    print("sssssssffffffffffffffffffffffffffffffff")
                    # print(count)
                    principal=obj.final_amt_given/interest_balance_sheet.interest.interest_period
                    print(principal)
                    # print(count.days * (interest_balance_sheet.interest.installment_amt))
                    if datetime.date.today() > terminating_date:
                        count= abs(((obj.interest_date + relativedelta(days=obj.paid_counts)))  - terminating_date)
                        return round((count.days) * (principal))
                    else:
                        print("saaleee")
                        days_check=abs((obj.interest_date + relativedelta(days=obj.paid_counts))  - datetime.date.today())
                        print(days_check)
                        return round(((days_check.days)-1) * (principal))


               

                        
                elif interest_balance_sheet.interest.interest_period_type=="Week":
                    principal=obj.final_amt_given/interest_balance_sheet.interest.interest_period

                    
                    paid_counts=obj.paid_counts
                    count= abs((obj.interest_date + relativedelta(days=obj.paid_counts)  - (datetime.date.today())))
                    print(count)
                    print("zzzzzzzzzzzzzzzzzzzzzzzzzzzzzz")
                    weeks = (count.days // 7) 
                    print(weeks)
                    print("uuuuuuuuuuuuuuuu")
                    days_cal=((obj.interest_date)  + relativedelta(weeks=weeks))
                    days_cal_limit=((obj.interest_date)  + relativedelta(weeks=weeks+1))
                    dates = []
                    current_date = days_cal
                    print(current_date)
                    while current_date >= days_cal and current_date < days_cal_limit:                                    
                        dates.append(current_date)
                        current_date += timedelta(days=1)
                    print(dates)
                    pay_date_check=CollectionDetails.objects.filter(interest=obj)
                    if pay_date_check:
                        pay_date_checking= CollectionDetails.objects.filter(interest=obj).last()
                        print("tttttttttt")
                        print(pay_date_checking)
                        if pay_date_checking.pay_date in dates: 
                            print(round(abs((weeks)-1) * ((interest_balance_sheet.interest.installment_amt))))
                            return round(abs((weeks)-1) * ((principal)))
                    else:
                        return round(abs((weeks)-1) * ((principal)))
                elif interest_balance_sheet.interest.interest_period_type=="Month":
                    print('yesyes')
                    principal=obj.final_amt_given/interest_balance_sheet.interest.interest_period

                    count= abs(((obj.interest_date + relativedelta(months=obj.paid_counts)))  - ((datetime.date.today())))
                    print(count)
                    print("hhhhhhhhhhhhhhhhhhhhhhh")
                    diff = relativedelta((((obj.interest_date + relativedelta(months=obj.paid_counts))), ((date.today()))))
                    month_diff = diff.years * 12 + diff.months
                    # month_diff=int(count.days/30)
                    print(month_diff)
                    pay_date_check=CollectionDetails.objects.filter(interest=obj)
                    if pay_date_check:
                        pay_date_checking=CollectionDetails.objects.filter(interest=obj).last()
                        if pay_date_checking.pay_date.month == (datetime.date.today().month) and pay_date_checking.pay_date.year == (datetime.date.today().year):

                            return round(((month_diff)) * ((principal)))

                    else:
                        return round(((month_diff)-1) * ((principal))) 