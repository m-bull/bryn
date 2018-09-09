from django.shortcuts import render
from django.contrib.auth.forms import AuthenticationForm
from userdb.forms import InvitationForm
from django.http import HttpResponseRedirect, HttpResponseBadRequest,\
    JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django_slack import slack_message

from userdb.models import Team, Region, TeamMember
from openstack.models import Tenant, get_tenant_for_team, ActionLog
from forms import LaunchServerForm, LaunchImageServerForm, RegionSelectForm
from scripts.list_instances import list_instances
from scripts.list_volumes import list_volumes
from scripts.gvl_launch import launch_gvl
from scripts.image_launch import launch_image

from .utils import messages_to_json

@login_required
def home(request):
    region = request.user.userprofile.current_region
    invite = InvitationForm(request.user)
    teams = Team.objects.filter(teammember__user=request.user)

    regionform = RegionSelectForm()
    regionform.initial['region'] = region

    for t in teams:
        team_member = TeamMember.objects.get(team=t, user=request.user)
        if request.user == t.creator or team_member.is_admin:
            t.is_admin = True
        t.active = True

        ## check if region is available
        if region.disabled:
            messages.error(request, 'The %s region is currently unavailable. Check the community forum for service status.' % (region.name))
            t.active = False
            continue

        tenant = get_tenant_for_team(t, region)
        if not tenant:
            t.active = False
            slack_message(
                'home/slack/no_tenant_for_region.slack',
                {'team': t, 'region': region, 'user': request.user})
            continue

        if region.name == 'bham':
            t.horizon_endpoint = 'https://birmingham.climb.ac.uk'
        elif region.name == 'cardiff':
            t.horizon_endpoint = 'https://cardiff.climb.ac.uk'
        elif region.name == 'warwick':
            t.horizon_endpoint = 'http://stack.warwick.climb.ac.uk'
        elif region.name == 'swansea':
            t.horizon_endpoint = 'https://swansea.climb.ac.uk'

        try:
            t.launch_form = LaunchServerForm(tenant.get_flavors())
            available_keys = [key for key in tenant.get_keys() if key[0] != "cloudman"]
            t.launch_custom_form = LaunchImageServerForm(tenant.get_images(),tenant.get_flavors(), available_keys)
            t.tenant_access = tenant
            t.instances = list_instances(tenant)
            t.volumes = list_volumes(tenant, t.instances)
        except Exception, e:
            messages.error(
                request,
                'The %s region is currently unavailable. Check the community '
                'forum for service status.' % (region.name))
            slack_message(
               'home/slack/region_api_exception.slack',
                {
                    'team': t,
                    'region': region,
                    'user': request.user,
                    'e': e
                })

    context = {
        'invite': invite,
        'teams': teams,
        'region': region,
        'regionform': regionform
    }
    return render(request, 'home/dashboard.html', context)


@login_required
def get_instances_table(request):
    if request.is_ajax():
        team = get_object_or_404(Team, pk=request.GET.get('team_id'))
        if not team.teammember_set.filter(user=request.user):
            return HttpResponseBadRequest
        tenant = get_tenant_for_team(team, request.user.userprofile.current_region)
        if tenant:
            team.instances = list_instances(tenant)
        html = render_to_string(
            'home/includes/instances_table.html',
            {'t': team})
        return JsonResponse({'instances_table': html})
    else:
        return HttpResponseBadRequest

@login_required
def get_volumes_table(request):
    if request.is_ajax():
        team = get_object_or_404(Team, pk=request.GET.get('team_id'))
        if not team.teammember_set.filter(user=request.user):
            return HttpResponseBadRequest
        tenant = get_tenant_for_team(team, request.user.userprofile.current_region)
        if tenant:
            team.instances = list_instances(tenant)
            team.volumes = list_volumes(tenant, team.instances)
        html = render_to_string(
            'home/includes/volumes_table.html',
            {'t': team})
        return JsonResponse({'volumes_table': html})
    else:
        return HttpResponseBadRequest

def validate_and_get_tenant(request, teamid):
    team = get_object_or_404(Team, pk=teamid)

    # check belongs to team
    member = TeamMember.objects.filter(team=team, user=request.user)
    if not member:
        messages.error(request, 'Access denied to this team.')
        return HttpResponseRedirect('/')

    region = request.user.userprofile.current_region
    tenant = get_tenant_for_team(team, region)
    return tenant


def launch_server(request, launch_type, tenant, server_name, *args, **kwargs):
    log = ActionLog(tenant=tenant, user=request.user)

    if tenant.region.disable_new_instances:
        messages.error(
            request,
            'Launching new instances is temporarily disabled for this region (%s)'
            % tenant.region.name)
        return

    try:
        if launch_type == 'gvl':
            launch_gvl(tenant, server_name, *args, **kwargs)
            log.message = (
                "Name: {server_name}, Flavour: {flavour}, Image: GVL".format(
                    server_name=server_name,
                    flavour=args[1]
                )
            )
        elif launch_type == 'image':
            launch_image(tenant, server_name, *args, **kwargs)
            log.message = (
                "Name: {server_name}, Flavour: {flavour}, Image: {image}".format(
                    server_name=server_name,
                    flavour=args[3],
                    image=dict(tenant.get_images())[args[0]]
                )
            )
    except Exception, e:
        messages.error(request, 'Error launching: %s' % (e,))
        log.error = True
        log.message = e
    else:
        messages.success(request, 'Successfully launched server!')
        log.error = False
    log.save()


@login_required
def launch(request, teamid):
    tenant = validate_and_get_tenant(request, teamid)

    f = LaunchServerForm(tenant.get_flavors(), request.POST)
    if not f.is_valid():
        if request.is_ajax():
            return JsonResponse({'errors': f.errors}, status=400)
        messages.error(request, 'Problem with form items.')
        return render(request, 'home/launch-fail.html', context={'form': f})

    launch_server(request, 'gvl', tenant, f.cleaned_data['server_name'], f.cleaned_data['password'], f.cleaned_data['server_type'])

    if request.is_ajax():
        return JsonResponse(messages_to_json(request))
    else:
        return HttpResponseRedirect('/')


@login_required
def launchcustom(request, teamid):
    tenant = validate_and_get_tenant(request, teamid)

    if request.method == 'POST':
        f = LaunchImageServerForm(tenant.get_images(), tenant.get_flavors(),tenant.get_keys(), request.POST)
        if not f.is_valid():
            if request.is_ajax():
                return JsonResponse({'errors': f.errors}, status=400)
            messages.error(request, 'Problem with form items.')
        else:
            if f.cleaned_data['server_key_name_choice'] == u'bryn:new':
                key_name = f.cleaned_data['server_key_name']
                key_value = f.cleaned_data['server_key']
            else:
                key_name = f.cleaned_data['server_key_name_choice']
                key_value = ''
            launch_server(request, 'image', tenant, f.cleaned_data['server_name'], f.cleaned_data['server_image'], key_name, key_value, f.cleaned_data['server_type'])

        if request.is_ajax():
            return JsonResponse(messages_to_json(request))
        else:
            return HttpResponseRedirect('/')
    else:
        f = LaunchImageServerForm(tenant.get_images(), tenant.get_keys())
    return render(request, 'home/launch-image.html', context={'form' : f})


@login_required
def stop(request, teamid, uuid):
    tenant = validate_and_get_tenant(request, teamid)
    try:
        tenant.stop_server(uuid)
        messages.success(request, 'Server stopped.')
    except Exception, e:
        messages.error(request, e)
    if request.is_ajax():
        return JsonResponse(messages_to_json(request))
    else:
        return HttpResponseRedirect('/')


@login_required
def start(request, teamid, uuid):
    tenant = validate_and_get_tenant(request, teamid)
    try:
        tenant.start_server(uuid)
        messages.success(request, 'Server started.')
    except Exception, e:
        messages.error(request, e)
    if request.is_ajax():
        return JsonResponse(messages_to_json(request))
    else:
        return HttpResponseRedirect('/')


@login_required
def reboot(request, teamid, uuid):
    tenant = validate_and_get_tenant(request, teamid)
    try:
        tenant.reboot_server(uuid)
        messages.success(request, 'Server rebooted.')
    except Exception, e:
        messages.error(request, e)
    if request.is_ajax():
        return JsonResponse(messages_to_json(request))
    else:
        return HttpResponseRedirect('/')


@login_required
def terminate(request, teamid, uuid): 
    tenant = validate_and_get_tenant(request, teamid)
    try:
        tenant.terminate_server(uuid)
        messages.success(request, 'Server terminated.')
    except Exception, e:
        messages.error(request, e)
    if request.is_ajax():
        return JsonResponse(messages_to_json(request))
    else:
        return HttpResponseRedirect('/')

def shelve(request, teamid, uuid):
    tenant = validate_and_get_tenant(request, teamid)
    try:
        tenant.shelve_server(uuid)
        messages.success(request, 'Server shelved.')
    except Exception, e:
        messages.error(request, e)
    if request.is_ajax():
        return JsonResponse(messages_to_json(request))
    else:
        return HttpResponseRedirect('/')


def unshelve(request, teamid, uuid): 
    tenant = validate_and_get_tenant(request, teamid)
    try:
        tenant.unshelve_server(uuid)
        messages.success(request, 'Server unshelved.')
    except Exception, e:
        messages.error(request, e)
    if request.is_ajax():
        return JsonResponse(messages_to_json(request))
    else:
        return HttpResponseRedirect('/')

@login_required
def region_select(request):
    if request.method == 'POST':
        f = RegionSelectForm(request.POST)
        if f.is_valid():
            userprofile = request.user.userprofile
            userprofile.current_region = f.cleaned_data['region']
            userprofile.save()
            messages.success(request, 'Region changed to %s' % (f.cleaned_data['region']))

    return HttpResponseRedirect('/')


def status(request):
    regions = Region.objects.all()
    return render(request, 'home/status.html', context={'regions' : regions})
