from rest_framework import serializers

from client.model.clientmanage import Client, Site, SiteImage


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = [
            "id",
            "first_name",
            "last_name",
            "phone",
            "email",
        ]


class SiteImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteImage
        fields = ["id", "image"]



class SiteSerializer(serializers.ModelSerializer):
    site_image = serializers.ListField(
        child=serializers.ImageField(max_length=1000000, allow_empty_file=False, use_url=False),
        required=False,
        write_only=True,
    )
    images = SiteImageSerializer(many=True, read_only=True)

    class Meta:
        model = Site
        fields = [
            "id",
            "name",
            "address",
            "cleaning_frequency",
            "price",
            "client_id",
            "cleaning_instructions",
            "site_image",
            "images",
            "assigned_contractor",
        ]

    def create(self, validated_data):
        uploaded_images = validated_data.pop("site_image", [])
        site = Site.objects.create(**validated_data)

        for image in uploaded_images:
            SiteImage.objects.create(site=site, image=image)

        return site


class ClientSiteSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = [
            "id",
            "name",
            "address",
            "cleaning_frequency",
            "price",
            "cleaning_instructions",
        ]


class ClientSiteSerializer(serializers.ModelSerializer):
    sites = ClientSiteSummarySerializer(many=True, read_only=True)

    class Meta:
        model = Client
        fields = [
            "id",
            "first_name",
            "last_name",
            "phone",
            "email",
            "sites",
        ]


class UpdateSiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = [
            "id",
            "name",
            "address",
            "cleaning_frequency",
            "price",
            "client_id",
            "cleaning_instructions",
            "assigned_contractor",
        ]

class GetSiteSerializer(serializers.ModelSerializer):
    client = ClientSerializer(source="client_id", read_only=True)
    site_images = SiteImageSerializer(source="images", many=True, read_only=True)
    class Meta:
        model = Site
        fields = [
            "id",
            "name",
            "address",
            "cleaning_frequency",
            "price",
            "cleaning_instructions",
            "client",
            "site_images",
        ]




