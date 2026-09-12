from rest_framework import serializers
from .models import PeopleInterestDetails
from rest_framework.exceptions import ValidationError
from django.utils import timezone
import datetime
from balancesheet.models import PeopleInterestBalanceSheet
from dateutil.relativedelta import relativedelta
from datetime import date, timedelta
from collection.models import CollectionDetails




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
                    # ------------------------------------------------------------------
                    # Percentage guard: hard-cap Fix Interest Rate and Penalty at 100 %
                    # when the caller selected percentage mode.
                    # ------------------------------------------------------------------
                    rate_type = validated_data.get("interest_type_new")
                    fix_rate = validated_data.get("fix_interest_rate_percent")
                    if (
                        rate_type == "percentage"
                        and fix_rate is not None
                        and float(fix_rate) > 100
                    ):
                        raise serializers.ValidationError({
                            "fix_interest_rate_percent":
                                "Fix Interest Rate percentage cannot exceed 100%.",
                        })

                    penalty_type = validated_data.get("penalty_type")
                    penalty_amount = validated_data.get("penalty_amount")
                    if (
                        penalty_type == "percentage"
                        and penalty_amount is not None
                        and float(penalty_amount) > 100
                    ):
                        raise serializers.ValidationError({
                            "penalty_amount":
                                "Penalty percentage cannot exceed 100%.",
                        })
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
        # FIX (Feb 2026): the previous implementation computed a
        # different, incorrect figure per interest_category:
        #   - "Interest": returned intrest_balance_amt - obj.interest_amt,
        #     which ignored principal_balance and penalty_balance_amt
        #     entirely, and produced 0 or negative values whenever the
        #     borrower's current-period interest matched interest_amt.
        #   - "Interest with capital": no branch existed at all, so this
        #     always returned None (falls through to the implicit
        #     `return None` at the end of the function) — the "Total
        #     Balance Amount" field on the frontend showed blank/NaN.
        #   - "Installment Interest": reconstructed an estimate from
        #     interest_date/paid_counts date arithmetic, entirely
        #     disconnected from principal_balance / intrest_balance_amt /
        #     penalty_balance_amt actually maintained by every payment
        #     path in collection/views.py — never included penalty, and
        #     could drift from the real ledger on partial payments,
        #     overpayments, or discount-waived collections.
        #
        # Every collection/payment/reversal branch elsewhere in this
        # codebase (add_collection_details, edit_collections_details,
        # the overdue accrual engine in interest/overdue_views.py) reads
        # and writes principal_balance, intrest_balance_amt, and
        # penalty_balance_amt as the authoritative outstanding-balance
        # fields for ALL three interest_category values uniformly. This
        # replaces the three divergent, category-specific calculations
        # with a single explicit sum of those three fields — which is
        # what "Total Balance Amount" actually means everywhere else in
        # the app.
        interest_balance_sheet = PeopleInterestBalanceSheet.objects.filter(interest=obj).first()
        if not interest_balance_sheet:
            return None
        return (
            float(interest_balance_sheet.principal_balance or 0)
            + float(interest_balance_sheet.intrest_balance_amt or 0)
            + float(interest_balance_sheet.penalty_balance_amt or 0)
        )