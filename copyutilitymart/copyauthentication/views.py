from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from .utils import TokenGenerator, generate_token
from django.utils.encoding import force_bytes, force_str, DjangoUnicodeDecodeError
from django.core.mail import send_mail
from django.conf import settings
from django.views.generic import View
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str


# Create your views here.
def signin(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['pass1']
        confirm_password = request.POST['pass2']
        if password != confirm_password:
            messages.warning(request, "Passwords do not match")
            return render(request, 'test/signin.html')

        try:
            if User.objects.get(username=email):
                messages.info(request, 'Email is taken')
                return render(request, 'test/signin.html')
        except User.DoesNotExist:
            pass

        user = User.objects.create_user(email, email, password)
        user.is_active = False
        user.save()
        
        email_subject = "Activate Your Account"
        message = render_to_string('test/activate.html', {
            'user': user,
            'domain': '127.0.0.1:8000',
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': generate_token.make_token(user)
        })
        
        try:
            send_mail(
                email_subject,
                message,
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
            messages.success(request, 'Activate your account by clicking the link in your email')
        except Exception as e:
            messages.warning(request, f"Could not send email. Please try again later. Error: {str(e)}")
            # For development, show the activation link
            if settings.DEBUG:
                messages.info(request, f"Development mode: Activation link: {message}")
        
        return redirect('/auth/login/')
    return render(request, 'test/signin.html')




class ActivateAccountView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, DjangoUnicodeDecodeError):
            user = None

        if user is not None and generate_token.check_token(user, token):
            user.is_active = True
            user.save()
            messages.info(request, 'Account activated successfully')
            return redirect('/auth/login/')
        return render(request, 'test/activatefail.html')

def handlelogin(request):
    if request.method == 'POST':
        username = request.POST['email']    
        userpassword = request.POST['pass1']
        myuser = authenticate(username = username, password = userpassword)
        
        if myuser is not None:
            login(request,myuser)
            messages.success(request, "Successfully logged in")
            return redirect('/')
        
        else:
            messages.error(request,"Invalid credentials, please try again")
            return redirect('/auth/login/')
        
    return render(request,'test/login.html')
        
        


def handlelogout(request):
    logout(request)
    messages.info(request, "Successfully logged out")
    return redirect('/')



class RequestResetEmailView(View):
    def get(self,request):
        return render(request,'test/request-reset-email.html')
    
    def post(self,request):
        email=request.POST['email']
        user=User.objects.filter(email=email)

        if user.exists():
            email_subject='[Reset Your Password]'
            message=render_to_string('test/reset-user-password.html',{
                'domain':'127.0.0.1:8000',
                'uid':urlsafe_base64_encode(force_bytes(user[0].pk)),
                'token':PasswordResetTokenGenerator().make_token(user[0])
            })

            try:
                send_mail(
                    email_subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False,
                )
                messages.success(request, "We have sent you an email with instructions on how to reset your password")
            except Exception as e:
                messages.error(request, f"Could not send email. Please try again later. Error: {str(e)}")
                if settings.DEBUG:
                    messages.info(request, f"Development mode: Reset link: {message}")
            
            return render(request,'test/request-reset-email.html')
        else:
            messages.error(request, "No user found with this email address")
            return render(request,'test/request-reset-email.html')

class SetNewPasswordView(View):
    template_name = 'test/set-new-password.html'

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            context = {
                'uidb64': uidb64,
                'token': token
            }
            return render(request, self.template_name, context)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            messages.error(request, "Invalid password reset link")
            return redirect('login')

    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            
            password = request.POST.get('pass1')
            confirm_password = request.POST.get('pass2')

            if password != confirm_password:
                messages.error(request, "Passwords do not match")
                return render(request, self.template_name, {
                    'uidb64': uidb64,
                    'token': token
                })

            user.set_password(password)
            user.save()
            messages.success(request, "Password reset successful. Please login with your new password.")
            return redirect('login')

        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            messages.error(request, "Invalid password reset link")
            return redirect('login')
