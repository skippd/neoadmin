from django.shortcuts import render,redirect
from neomodel import db
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
import pandas as pd
import json
from django.conf import settings

# import logging
# logger = logging.getLogger(__name__)

home_url = settings.NEOADMIN_HOME

@login_required(login_url='/admin')
@user_passes_test(lambda u: u.is_superuser)
def index(request):
    k = db.cypher_query('MATCH (n) RETURN DISTINCT labels(n)[0] , count(labels(n))')
    m = db.cypher_query('match (a)-[r]->(m) return distinct labels(a)[0],TYPE(r),labels(m)[0],count(r)')
    # isolates = db.cypher_query('match (r) where not (r)-[]-() return r.name,ID(r),labels(r)')
    isolated = db.cypher_query('match (r) where not (r)-[]-() return count(r)')[0][0][0]
    nodedata = []
    tnodes = 0
    reldata = []
    trels = 0
    for i in k[0]:
        nodedata.append({"name":i[0],"count":i[1]})
        tnodes+=i[-1]
    for i in m[0]:
        reldata.append({"s":i[0],"r":i[1],"d":i[2],"c":i[3]})
        trels+=i[-1]
    config = db.cypher_query('call dbms.listConfig yield name, value, dynamic')
    return render(request,'index.html',{"nodedata":nodedata,"reldata":reldata,"isolated":isolated,"totalrels":trels,"home":home_url,"config":config[0]})


@login_required(login_url='/admin')
@user_passes_test(lambda u: u.is_superuser)
def label(request,labelstr=''):
    labli = labelstr.split('@')
    label = labli[0]
    rstr =' '
    for i in labli[1:]:
        rstr +=', p.'+i
    if label=='isolated':
        k = db.cypher_query('match (p) where not (p)-[]-() return ID(p)'+rstr+',labels(p)[0]')
        labli.pop(0)
        labli.append('label')
        head = labli
    else:
        k = db.cypher_query('match (p:'+label+') return ID(p)'+rstr)
        head = labli[1:]
    return render(request,'label.html',{"labels":k[0],"label":label,"headings":head,"home":home_url})


@login_required(login_url='/admin')
@user_passes_test(lambda u: u.is_superuser)
def relation(request,relstr='',sources=''):
    relli = relstr.split('@')
    relation = relli[0]
    if len(relli)>=2:
        count = relli[1]
    else:
        count = 200000
    fields = sources.split('@')
    # if len(fields)==3:
    #     skip = fields[2]
    if int(count) <= 100:
        k = db.cypher_query('match (a:'+fields[0]+')-[r:'+relation+']->(m:'+fields[1]+')  return a.name,ID(a),m.name,ID(m)')
        return render(request,'relation.html',{"relations":k[0],"label":relation,"headings":[fields[0],'Relation Name',fields[1]],"home":home_url})
    else:
        return render(request,'relationsearch.html',{"relations":[],"label":relation,"headings":[fields[0],relation,fields[1]],"home":home_url})


@login_required(login_url='/admin')
@user_passes_test(lambda u: u.is_superuser)
def search(request):
    if request.method == "POST":
        searchstr = request.POST.get("searchstr", "")
        error = ""
        if searchstr == "" or searchstr == "0" or searchstr == {}:
            error = "something wrong, Update Failed"
            return render(request,'nodedataedit.html',{"home":home_url,"error":error})
        query = "MATCH (r) WHERE r.name =~'(?i).*"+searchstr+".*' return ID(r),r.name,labels(r)[0]"
        k = db.cypher_query(query)
        return render(request,'nodesearch.html',{"home":home_url,"nodeinfo":k[0],"heading":['Id','Name','Label'],"searchstr":searchstr})
    if request.method == "GET":
        return render(request,'nodesearch.html',{"home":home_url})

@login_required(login_url='/admin')
@user_passes_test(lambda u: u.is_superuser)
def createnode(request):
    if request.method == 'POST':
        label = request.POST.get("label", "")
        pars = request.POST.get("datastr", "")
        if pars == "" or pars == "0" or pars == {}:
            error = "something wrong, Update Failed"
            return (request,"error.html",{"home":home_url,"error":error,"label":"Error"})
        pars = json.loads(pars)
        # create (n:Account) set n+={name:"test 23"} return ID(n)
        query = 'create (n:'+label+') SET n+=$pars RETURN ID(n)'
        onode = db.cypher_query(query,{'pars':pars})
        return redirect('{home}node/{id}'.format(home=home_url,id=onode[0][0][0]))

    if request.method == 'GET':
        lablist = db.cypher_query('match (m) return distinct labels(m)[0]')
        return render(request,'createnode.html',{"home":home_url,"lablist":lablist[0]})
    return

@login_required(login_url='/admin')
@user_passes_test(lambda u: u.is_superuser)
def relaction(request,action='',relid='',nodeid=''):
    if action=='deleteall':
        rr = db.cypher_query('MATCH (a)-[r]-() where ID(a) ='+nodeid+' delete r')
        return redirect('{home}node/{id}'.format(home=home_url,id=nodeid))
    if action=='deletenode':
        rr = db.cypher_query('MATCH (a)-[r]-() where ID(a) ='+nodeid+' delete r')
        k = db.cypher_query('MATCH (a)  where ID(a) ='+nodeid+' delete a')
        return redirect(home_url)
    if action=='delete':
        if relid==0 or relid=='':
            error = "no relation id to delete"
            return (request,"error.html",{"home":home_url,"error":error,"label":"Error"})
        rr = db.cypher_query('MATCH ()-[r]-() WHERE id(r)='+relid+' DELETE r')
        return redirect('{home}node/{id}'.format(home=home_url,id=nodeid))

    if action=='create':
        if request.method == 'POST':
            source = request.POST.get("source", "")
            relation = request.POST.get("relation", "")
            direction = request.POST.get("direction", "")
            destinationlist = request.POST.getlist('destination[]')
            querystart = 'MATCH (a),(b) WHERE ID(a) ='+source+'  AND ID(b) in ['
            if direction=='ltr':
                queryend = ']  CREATE (a)-[r:'+relation+']->(b) RETURN a'
            if direction=='rtl':
                queryend = ']  CREATE (a)<-[r:'+relation+']-(b) RETURN a'
            # logger.error("query is ",query)
            for i in destinationlist[:-1]:
                querystart = querystart+i+','
            querystart = querystart + destinationlist[-1]
            query = querystart+queryend
            # destination = [int(i) for i in destinationlist]
            # logger.error(query)

            rr = db.cypher_query(query)
            return redirect('{home}node/{id}'.format(home=home_url,id=nodeid))
            # return Http
        if request.method == 'GET':
            return redirect('{home}node/{id}'.format(home=home_url,id=nodeid))

    if action=='createpage':
        source = request.POST.get("source", "")
        relation = request.POST.get("relation", "")
        deslabel= request.POST.get("destination", "")
        direction= request.POST.get("direction", "")
        relfield = False
        if relation == 'NewRelation':
            relfield = True
        rr = db.cypher_query('MATCH (r:'+deslabel+') return ID(r),r.name ',{'relid':relid})
        return render(request,'relcreate.html',{"home":home_url,"relation":relation,"source":source,"lablist":rr[0],"relfield":relfield,"direction":direction})
    return

@login_required(login_url='/admin')
@user_passes_test(lambda u: u.is_superuser)
def nodeedit(request,nodeid=''):
    if request.method == "POST":
        pars = request.POST.get("datastr", "")
        error = ""
        if pars == "" or pars == "0" or pars == {}:
            error = "something wrong, Update Failed"
        pars = json.loads(pars)
        query = 'MATCH (r) where ID(r)='+str(nodeid)+' SET r=$pars RETURN r,r.name'
        onode = db.cypher_query(query,{'pars':pars})
        error ="updated the node"
        return render(request,'nodedataedit.html',{"home":home_url,"label":onode[0][0][1],"id":nodeid,"nodeinfo":json.dumps(onode[0][0][0].__dict__['_properties']),"error":error})
    if request.method == "GET":

        onode = db.cypher_query('MATCH (r) where ID(r)='+str(nodeid)+' RETURN r,r.name')

        return render(request,'nodedataedit.html',{"home":home_url,"label":onode[0][0][1],"id":nodeid,"nodeinfo":json.dumps(onode[0][0][0].__dict__['_properties'])})

@login_required(login_url='/admin')
@user_passes_test(lambda u: u.is_superuser)
def nodeview(request,nodeid=''):
    query ="MATCH (r)<-[re]->(m) where ID(r)="+str(nodeid)+" RETURN r.name,Type(re),ID(re),m.name,ID(m)"
    k = db.cypher_query(query)
    df = pd.DataFrame(k[0],columns=['node','rel','relid','dest','destid'])
    gby = df.groupby('rel')
    rels = []
    for group_name, df_group in gby:
        rels.append({"name":group_name,"items":list(zip(df_group['relid'],df_group['dest'],df_group['destid']))})
    onode = db.cypher_query('MATCH (r) where ID(r)='+str(nodeid)+' RETURN r,r.name')
    relsdata = db.cypher_query('match ()-[r]-(m) return distinct type(r),labels(m)[0]')
    rellist = []
    lablist = []
    for i in relsdata[0]:
        rellist.append(i[0])
        lablist.append(i[1])
    return render(request,'nodedit.html',{"relations":rels,"label":onode[0][0][1],"id":nodeid,"home":home_url,"nodeinfo":onode[0][0][0],"relist":list(set(rellist)),"lablist":list(set(lablist))})


@login_required(login_url='/admin')
@user_passes_test(lambda u: u.is_superuser)
def relationsearch(request,relation='',source='',sourcestr='',destination='',destinationstr='',skip=0):
    if sourcestr!='none' or destinationstr!='none':
        wherestr = ''
        if sourcestr!='none':
            wherestr+=" s.name =~'(?i).*"+sourcestr+".*' "
        if destinationstr!='none':
            if wherestr!='':
                wherestr += ' or'
            wherestr+=" d.name =~'(?i).*"+destinationstr+".*' "
        query = 'match (s:'+source+')-[r:'+relation+']->(d:'+destination+') WHERE '+wherestr+' return s.name,ID(s),d.name,ID(d)'
        k = db.cypher_query(query)

        return render(request,'relationsearch.html',{"relations":k[0],"label":relation,"headings":[source,relation,destination],"home":home_url})

    else:
        return render(request,'relationsearch.html',{"relations":[],"label":relation,"headings":[source,relation,destination],"home":home_url})
