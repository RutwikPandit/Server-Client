#include<bits/stdc++.h>
using namespace std;

typedef struct _no
{
	int val;
	struct _no *next;
}node;
int n,s;

void insert(node ** hasht,int key)
{
	int k=key%s;
	node *ptr;
	ptr=(node *)malloc(sizeof(node));
	ptr->val=key;
	ptr->next=hasht[k];
	hasht[k]=ptr;
}

int search()
{

}

int main()
{
	int i,k;
	node **hasht,*p;
	scanf("%d %d",&s,&n);
	hasht=(node**)malloc(s*sizeof(node*));
	for(i=0;i<s;i++)
		hasht[i]=NULL;
	for(i=0;i<n;i++)
	{
		scanf("%d",&k);
		insert(hasht,k);
	}
	for(i=0;i<s;i++)
	{
		p=hasht[i];
		printf("%d ",i );
		while(p!=NULL)
		{
			printf("%d ",p->val);
			p=p->next;
		}
		printf("\n");
	}



	return 0;
}
