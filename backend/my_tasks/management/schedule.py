from apscheduler.schedulers.background import BackgroundScheduler
from django.core.mail import send_mail
# from django.contrib.auth.models import User
# from user_subscribtion.models import UserSubscribeDetails,Subscription
import datetime
# from datetime import datetime,date
# from user_subscribtion.views import subscription_delete
 # Import the task you created

scheduler = BackgroundScheduler()

# my_date=datetime.datetime.now()
    
def subscription():
    from my_tasks.views import subscription_delete
    subscription_delete() 

   


def start():
    # scheduler.add_job(my_task, 'interval', days=1, start_date='2023-10-04 10:20:00') 
    # working
    scheduler.add_job(subscription,'interval', days=1, start_date='2023-10-04 19:30:00') 
    
    # scheduler.add_job(subscription,'interval', days=1, start_date=my_date) 
    
    scheduler.start()