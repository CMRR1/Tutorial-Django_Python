#from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import Board, Topic, Post
from django.contrib.auth.models import User
from .forms import NewTopicForm, PostForm
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.views.generic import UpdateView, ListView
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger



# Create your views here.
def home(request):
  #  boards = Board.objects.all()
  #  boards_names=list()

    # for board in boards:
    # boards_names.append(board.name)
    #response_html='<br>'.join(boards_names)
    #return HttpResponse(response_html)

    #UPDATE
    boards=Board.objects.all()
    return render(request,'home.html',{'boards':boards})
    

#Creando los topics.
def board_topics(request, pk):
    board = get_object_or_404(Board, pk=pk)
    queryset = board.topics.order_by('-last_updated').annotate(replies=Count('posts') - 1)
    page = request.GET.get('page', 1)

    paginator = Paginator(queryset, 20)

    try:
        topics = paginator.page(page)
    except PageNotAnInteger:
        # fallback to the first page
        topics = paginator.page(1)
    except EmptyPage:
        # probably the user tried to add a page number
        # in the url, so we fallback to the last page
        topics = paginator.page(paginator.num_pages)

    return render(request, 'topics.html', {'board': board, 'topics': topics})

#Creando un nuevo topic.
@login_required
def new_topic(request, pk):
  board=get_object_or_404(Board, pk=pk)
  user=User.objects.first()
  
  if request.method =='POST':
    subject=request.POST['subject']
    message=request.POST['message']
    
    form=NewTopicForm(request.POST)
    if form.is_valid():
      topic=form.save(commit=False)
      topic.board=board
      topic.starter=request.user
      topic.save()
      post=Post.objects.create(
        message=form.cleaned_data.get('message'),
        topic=topic,
        created_by=request.user
      )
    return redirect('topic_posts', pk=pk, topic_pk=topic.pk)
  else:
    form=NewTopicForm()
  
  return render(request, 'new_topic.html', {'board':board, 'form':form})


#Aqui se crean los post de los topics.
def topic_posts(request, pk, topic_pk):
    topic = get_object_or_404(Topic, board__pk=pk, pk=topic_pk)
    return render(request, 'topic_posts.html', {'topic': topic})
  

#Aqui se crea el reply o replica del post.
@login_required
def reply_topic(request, pk, topic_pk):
    topic = get_object_or_404(Topic, board__pk=pk, pk=topic_pk)
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.topic = topic
            post.created_by = request.user
            post.save()
            topic.last_updated = timezone.now()
            topic.save()
            return redirect('topic_posts', pk=pk, topic_pk=topic_pk)
    else:
        form = PostForm()
    return render(request, 'reply_topic.html', {'topic': topic, 'form': form})
  
  
#Aqui se actualiza el post.
@method_decorator(login_required, name='dispatch')
class PostUpdateView(UpdateView):
    model = Post
    fields = ('message', )
    template_name = 'edit_post.html'
    pk_url_kwarg = 'post_pk'
    context_object_name = 'post'

    def form_valid(self, form):
        post = form.save(commit=False)
        post.updated_by = self.request.user
        post.updated_at = timezone.now()
        post.save()
        return redirect('topic_posts', pk=post.topic.board.pk, topic_pk=post.topic.pk)
      
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(created_by=self.request.user)  
      
      
class BoardListView(ListView):
    model = Board
    context_object_name = 'boards'
    template_name = 'home.html'
    
    
class TopicListView(ListView):
    model = Topic
    context_object_name = 'topics'
    template_name = 'topics.html'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        kwargs['board'] = self.board
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        self.board = get_object_or_404(Board, pk=self.kwargs.get('pk'))
        queryset = self.board.topics.order_by('-last_updated').annotate(replies=Count('posts') - 1)
        

class PostListView(ListView):
    model = Post
    context_object_name = 'posts'
    template_name = 'topic_posts.html'
    paginate_by = 2

    def get_context_data(self, **kwargs):
        session_key = 'viewed_topic_{}'.format(self.topic.pk) 
        if not self.request.session.get(session_key, False):
            self.topic.views += 1
            self.topic.save()
            self.request.session[session_key] = True  

        kwargs['topic'] = self.topic
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        self.topic = get_object_or_404(Topic, board__pk=self.kwargs.get('pk'), pk=self.kwargs.get('topic_pk'))
        queryset = self.topic.posts.order_by('created_at')
        return queryset
      
      
      
#En vista que el pagination no me sirvio, me e visto en la tarea de
#hacer mi propio pagination buscado de internet.
def index(request):
    topics = Topic.objects.all() #queryset containing all topics we just created
    paginator = Paginator(topics, 3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request=request, template_name="templates/topics.html", context={'movies':page_obj})