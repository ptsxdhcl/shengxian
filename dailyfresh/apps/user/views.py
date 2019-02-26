from django.shortcuts import render,redirect
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate,login
from django.http import HttpResponse
from django.core.mail import send_mail
from user.models import User
from celery_tasks.tasks import send_register_active_email
from django.views.generic import View
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
import re





# user/register
class RegisterView(View):
    '''注册类'''
    def get(self,request):
        '''显示注册页面'''
        return render(request,'register.html')

    def post(self,request):
        '''进行注册处理'''
        # 接收数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 进行数据校验
        if not all([username, password, email]):
            # 数据不完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})

        # 校验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在
            user = None

        if user:
            # 用户名已存在
            return render(request, 'register.html', {'errmsg': '用户名已存在'})

        # 进行业务处理: 进行用户注册
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        # 发送激活邮件，包含激活链接：http:/127.0.0.1:8000/user/active/id..
        # 激活链接中需要包含用户的身份信息，并且需要加密，
        # 加密用户身份信息，生成激活token
        serializer = Serializer(settings.SECRET_KEY,3600)
        info = {'confirm':user.id}
        token = serializer.dumps(info) # bytes类型
        token = token.decode()         # 转为字符串类型
 
        # 发邮件
        send_register_active_email.delay(email, username, token)




        # 返回应答, 跳转到首页
        return redirect(reverse('goods:index'))

# user/active/id
class ActiveView(View):
    '''用户激活'''
    def get(self,request,token):
        '''进行用户激活'''
        # 进行解密，获取要激活的用户信息
        serializer = Serializer(settings.SECRET_KEY,3600)
        try:
            info = serializer.loads(token)
            # 获取待激活用户的id
            user_id = info['confirm']
            # 根据用户id获取用户信息
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()
            # 跳转到登陆页面
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            # 激活链接已过期，实际项目中要重新发送链接
            return HttpResponse('激活链接已过期')


# user/login
class LoginView(View):
    '''登陆'''
    def get(self,request):
        '''显示登陆页面'''
        return render(request,'login.html')

    def post(self,request):
        '''登陆校验'''
        # 接收数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        # 校验数据
        if not all([username,password]):
            return render(request,'login.html',{'errmsg':'数据不完整'})
        
        # 业务处理，登陆校验
        user = authenticate(username=username,password=password)
        if user is not None:
            # 用户名密码正确
            if user.is_active:
                # 用户已激活
                # 记录用户的登陆状态
                login(request,user)
                # 跳转到首页
                return redirect(reverse('goods:index'))

            else:
                # 用户未激活
                return render(request,'login.html',{'errmsg':'账户未激活'})  

        else:
            # 用户名或密码错误
            return render(request,'login.html',{'errmsg':'用户名或密码错误'})

































