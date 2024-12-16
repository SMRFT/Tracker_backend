from django.db import models
from django.contrib.auth.models import User

#Register Employee with email and password 
class Employee(models.Model):
    employeeId = models.CharField(max_length=50, primary_key=True)
    employeeName = models.CharField(max_length=100)
    employeeDepartment = models.CharField(max_length=100)
    employeeDesignation = models.CharField(max_length=100)
    email = models.EmailField(unique=True) 
    password = models.CharField(max_length=255) 

class Board(models.Model):
    boardId = models.PositiveIntegerField(unique=True, blank=True, editable=False,primary_key=True)
    boardName = models.CharField(max_length=255)
    boardColor = models.CharField(max_length=250)
    employeeId = models.CharField(max_length=50)
    employeeName = models.CharField(max_length=100)
    createdDate= models.DateField(auto_now_add=True)
    createdTime = models.TimeField(auto_now=True)
    def save(self, *args, **kwargs):
        if not self.boardId:
            # Get the highest existing boardId and increment by 1
            last_board = Board.objects.order_by('-boardId').first()
            if last_board and last_board.boardId is not None:
                self.boardId = last_board.boardId + 1
            else:
                self.boardId = 1
        super(Board, self).save(*args, **kwargs)
        

class Card(models.Model):
    boardId = models.PositiveIntegerField()
    boardName = models.CharField(max_length=255)
    employeeId = models.CharField(max_length=50)
    employeeName = models.CharField(max_length=255)
    cardId = models.PositiveIntegerField(unique=True, blank=True, editable=False, primary_key=True)
    cardName = models.CharField(max_length=255)
    columnId = models.CharField(max_length=50)
    description = models.TextField()
    comment = models.JSONField()  # (empid, empname, commenttext, date, time)
    startdate = models.DateField( blank=True)
    enddate = models.DateField( blank=True)
    members = models.JSONField()  # (empid, empname)
    createdDate = models.DateField(auto_now_add=True)
    createdTime = models.TimeField(auto_now=True)
    def save(self, *args, **kwargs):
        # Generate cardId if not present
        if not self.cardId:
            last_card = Card.objects.order_by('-cardId').first()
            if last_card and last_card.cardId is not None:
                self.cardId = last_card.cardId + 1
            else:
                self.cardId = 1

        # Fetch the current instance of the card from the database (before saving)
        old_card = Card.objects.filter(pk=self.pk).first()

        super(Card, self).save(*args, **kwargs)  # Save the card first

        # If the card is being updated, check for changes in members, description, and comments
        if old_card:
            if self.members != old_card.members:
                self.send_member_update_notification(old_card)
            if self.description != old_card.description:
                self.send_description_update_notification()
            if self.comment != old_card.comment:
                self.send_comment_update_notification()
    def send_member_update_notification(self, old_card):
        old_members = {m['employeeId'] for m in old_card.members}
        new_members = {m['employeeId'] for m in self.members}

        # Find newly added members
        added_members = new_members - old_members

        for member_id in added_members:
            Notification.objects.create(
                employeeId=member_id,
                cardId=self.cardId,
                message=f"You've been added to the card '{self.cardName}'.",
            )

        # Notify existing members of any changes in other members
        for member in old_members.union(new_members):
            Notification.objects.create(
                employeeId=member,
                cardId=self.cardId,
                message=f"Members have been updated in the card '{self.cardName}'.",
            )

    def send_description_update_notification(self):
        for member in self.members:
            Notification.objects.create(
                employeeId=member['employeeId'],
                cardId=self.cardId,
                message=f"The description for the card '{self.cardName}' has been updated.",
            )

    def send_comment_update_notification(self):
        for member in self.members:
            Notification.objects.create(
                employeeId=member['employeeId'],
                cardId=self.cardId,
                message=f"A new comment has been added to the card '{self.cardName}'.",
            )


class Notification(models.Model):
    employeeId = models.CharField(max_length=50)
    cardId = models.PositiveIntegerField()
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    createdDate = models.DateField(auto_now_add=True)
    createdTime = models.TimeField(auto_now=True)
