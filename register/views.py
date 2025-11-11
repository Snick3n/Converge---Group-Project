from django.shortcuts import render, redirect
from .forms import RegisterForm
from django.contrib.auth.models import User, Group

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            uname = form.cleaned_data['username']
            form.save()
            user = User.objects.get(username=uname)
            user.is_staff = False
            user.is_superuser = False
            goer_group, created = Group.objects.get_or_create(name='EventGoer')
            user.groups.add(goer_group)
            user.save()
            return redirect('login')
        return redirect('catalog:index')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


# Create your views here.
