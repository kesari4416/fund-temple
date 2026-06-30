from rest_framework.response import Response
import jwt
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from user.models import User

from rest_framework.decorators import api_view

def token_checking(request):
    token=request.headers.get('Authorization')
    if not token:
        raise AuthenticationFailed('Unauthenticated!')
    try:
        payload=jwt.decode(token,'secret',algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed('Unauthenticated!')
    except:
        return Response(status=status.HTTP_417_EXPECTATION_FAILED)
    user=User.objects.filter(id=payload['id']).first()
    if not user:
        return Response({"message":"No User Found"},status=status.HTTP_401_UNAUTHORIZED)
    if not user.is_active:
        return Response({"message":"Not Authorized Please Contact Admin"},status=status.HTTP_401_UNAUTHORIZED)
    return user








# @api_view(['GET'])
# def token_check(request):
#     if request.method == "GET":
      
#         token=request.headers.get('Authorization')
       
#         if not token:
         
#             raise AuthenticationFailed('Unauthenticated!')
#         try:
#             payload=jwt.decode(token,'secret',algorithms=['HS256'])
#         except jwt.ExpiredSignatureError:
        
#             rj_token=True   
#             response=Response()
#             response.data={
#                 'avenger':rj_token,

#             }
#             return response
#             # raise AuthenticationFailed('Unauthenticated!')
#         except:
#             return Response(status=status.HTTP_417_EXPECTATION_FAILED)
            
            
#         user=User.objects.filter(id=payload['id']).first()  
      
    
#         check_date=request.headers.get('Rejin')
#         if not check_date:
          
#             raise AuthenticationFailed('Unauthenticated!')
        
    
#         datetime_object = datetime.strptime(check_date, "%Y-%m-%dT%H:%M:%S.%f")

        
#         current=datetime.utcnow()
       
        
#         # Subtracting 30 minutes
#         time_delta = timedelta(hours=1,minutes=30)

#         # Subtracting the time delta from the datetime object
        
       
#         exp_result2 = datetime_object - time_delta
    
        
#         if exp_result2 <= current:
#             rj_token=True
         
#         else:
#             rj_token=False   
        
#         response=Response()
#         response.data={
#             'avenger':rj_token,

#         }
#         return response

   
import datetime
@api_view(['POST'])
def generate_token(request):
    if request.method == "POST":
        try:
            token1 = request.data['refresh']
            # Decode the expired token without verifying the signature
            decoded_token = jwt.decode(token1, options={"verify_signature": False})
            # Extract user ID from the decoded token
            user_id = decoded_token.get('id')
            # Fetch user from the database using the extracted user ID
            user = User.objects.filter(id=user_id).first()
            if user:
                payload = {
                    "id": user.id,
                    "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=1440),
                    "iat": datetime.datetime.utcnow(),
                }
                # Generate a new token for the user
                token = jwt.encode(payload,'secret',algorithm='HS256')
                response=Response()
                response.data = {
                    'jwt': token,
                    'username': user.name,
                    'email':user.email,
                }
                return response
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        except jwt.ExpiredSignatureError:
            # Handle expired token
            return Response({'error': 'Expired token'}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.InvalidTokenError:
            # Handle invalid token
            return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            # Handle other exceptions
            print(str(e))
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

