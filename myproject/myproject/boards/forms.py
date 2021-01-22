from django import forms
from .models import Topic, Post

#Aqui se crea el "formato/formulario" topic.
class NewTopicForm(forms.ModelForm):
    message = forms.CharField(
        widget=forms.Textarea(
            attrs={'row':5, 
                   'placeholder':'What is on you mind?'}), 
        max_length=4000,
        help_text='The max length of the text is 4000')

    class Meta:
        model = Topic
        fields = ['subject', 'message']


#Aqui se crea el formato para el post.
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['message', ]