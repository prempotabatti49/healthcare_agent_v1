# Sunflower - personalized AI health assistant app 
A personalized healthcare AI agent that leverages memory (episodic, semantic, and medical), RAG pipelines, and multi-agent reasoning to provide context-aware health guidance based on a user’s history, habits, and medical data.

![alt text](<sunflower-pic1 - Copy-1.png>)

# Story behind this app
I shifted to my hometown to move to Abu Dhabi. But because of war in west asia, my stay at home got extended. As I spent more time, I realized that my mom needs someone to take care. She keeps forgetting things. I wanted to build something for my mother to help her with her health issues. That's how this app is ideated. To help her with reminding her about her what doctor said to her and what kind of diet she prescribed her, reminding her to control certain foods if she feels tempted, basically a personalized friend who remembers many things about her. 
- Now, you can upload all medical reports, doctor's prescriptions, dietary restrictions, etc, so that sunflower can give personalized and holistic suggestions.

#### It also helped me
So, it also helped me fight social media doom scrolling. I kept coming back to instagram even after deciding to deactivate it for some time. Striking thing with social media was, I forget the reason for which I was deactivating my account. So, next time when I felt, let's watch it only for 1 hour - it takes up entire day. Then I remember, what a futile thing I did. This app, helped me remind the exact reason why I had deactivated, it reminded me the futulity of overestimating my self-control, and gave two or three examples of why I should not be installing instagram again. I was able to deactivate for 20 days, which was an achievement in itself for me.

#### It is designed to be your friendly assistant
It is designed to help you at physical and mental level with features like
- Identifying critical scenarios - if someone is facing suicidal thoughts
- Daily health positivity quotes
- Assist in physical health as well as mental health
- Understand medical reports


##  What you need to run this app:
- supermemory API key
- AWS account for DB management
- one secret key for auth management
- openAI API key or Claude API key (as per your preference)

## Steps
- Build the docker image
- Push it into ECR
- Create ALB and target group
- Create new ECS Fargate cluster and task definition
- Create new service and spin up tasks
