from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _


class Concert(models.Model):
    concert_name = models.CharField(max_length=200)
    duration = models.PositiveSmallIntegerField(help_text="Duration in minutes")
    city = models.CharField(max_length=120)
    date = models.DateField()

    class Meta:
        ordering = ("date", "concert_name")

    def __str__(self):
        return self.concert_name


class ConcertAttending(models.Model):
    class AttendingChoices(models.TextChoices):
        NOTHING = "-", _("-")
        NOT_ATTENDING = "Not Attending", _("Not Attending")
        ATTENDING = "Attending", _("Attending")

    concert = models.ForeignKey(Concert, on_delete=models.CASCADE, related_name="attendee")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    attending = models.CharField(
        max_length=100,
        choices=AttendingChoices.choices,
        default=AttendingChoices.NOTHING,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("concert", "user"), name="unique_concert_rsvp_per_user")
        ]

    def __str__(self):
        return f"{self.user.username}: {self.concert.concert_name} ({self.attending})"
