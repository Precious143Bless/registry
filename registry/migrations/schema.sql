--
-- Create model ParishInfo
--
CREATE TABLE `registry_parishinfo` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `parish_name` varchar(200) NOT NULL, `diocese` varchar(200) NOT NULL, `date_established` date NULL, `vision` longtext NOT NULL, `mission` longtext NOT NULL, `church_logo` varchar(100) NULL, `prime_bishop_name` varchar(200) NOT NULL, `prime_bishop_details` longtext NOT NULL, `prime_bishop_image` varchar(100) NULL, `street_address` varchar(255) NOT NULL, `barangay` varchar(100) NOT NULL, `municipality` varchar(100) NOT NULL, `province` varchar(100) NOT NULL, `zip_code` varchar(10) NOT NULL, `contact_number` varchar(20) NOT NULL, `email` varchar(254) NOT NULL);
--
-- Create model Church
--
CREATE TABLE `registry_church` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `name` varchar(200) NOT NULL, `location` varchar(300) NOT NULL, `description` longtext NOT NULL, `established_date` date NULL, `contact_number` varchar(20) NOT NULL, `email` varchar(254) NOT NULL, `bishop` varchar(200) NOT NULL, `image` varchar(100) NULL, `is_active` bool NOT NULL, `date_created` date NOT NULL, `date_updated` date NOT NULL);
--
-- Create model Cathedral
--
CREATE TABLE `registry_cathedral` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `name` varchar(200) NOT NULL, `location` varchar(300) NOT NULL, `description` longtext NOT NULL, `established_date` date NULL, `contact_number` varchar(20) NOT NULL, `email` varchar(254) NOT NULL, `is_active` bool NOT NULL, `date_created` date NOT NULL, `date_updated` date NOT NULL, `church_id` bigint NOT NULL UNIQUE);
--
-- Create model Parish
--
CREATE TABLE `registry_parish` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `name` varchar(200) NOT NULL, `location` varchar(300) NOT NULL, `description` longtext NOT NULL, `established_date` date NULL, `contact_number` varchar(20) NOT NULL, `email` varchar(254) NOT NULL, `is_active` bool NOT NULL, `date_created` date NOT NULL, `date_updated` date NOT NULL, `church_id` bigint NOT NULL);
--
-- Create model Member
--
CREATE TABLE `registry_member` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `first_name` varchar(100) NOT NULL, `middle_name` varchar(100) NOT NULL, `last_name` varchar(100) NOT NULL, `birthday` date NOT NULL, `gender` varchar(1) NOT NULL, `civil_status` varchar(20) NOT NULL, `address` longtext NOT NULL, `contact_number` varchar(20) NOT NULL, `email` varchar(254) NOT NULL, `is_active` bool NOT NULL, `date_registered` date NOT NULL, `user_id` integer NULL UNIQUE, `church_id` bigint NULL, `parish_id` bigint NULL);
--
-- Create model Organization
--
CREATE TABLE `registry_organization` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `name` varchar(200) NOT NULL, `description` longtext NOT NULL, `meeting_schedule` varchar(200) NOT NULL, `meeting_venue` varchar(200) NOT NULL, `contact_person` varchar(200) NOT NULL, `is_active` bool NOT NULL, `date_created` date NOT NULL, `date_updated` date NOT NULL);
--
-- Create model Baptism
--
CREATE TABLE `registry_baptism` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `date_baptized` date NOT NULL, `priest` varchar(150) NOT NULL, `godfathers` longtext NOT NULL, `godmothers` longtext NOT NULL, `birth_certificate_no` varchar(100) NOT NULL, `remarks` longtext NOT NULL, `member_id` bigint NOT NULL UNIQUE);
--
-- Create model Confirmation
--
CREATE TABLE `registry_confirmation` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `date_confirmed` date NOT NULL, `bishop` varchar(150) NOT NULL, `confirmation_name` varchar(100) NOT NULL, `sponsor` varchar(150) NOT NULL, `remarks` longtext NOT NULL, `member_id` bigint NOT NULL UNIQUE);
--
-- Create model FirstHolyCommunion
--
CREATE TABLE `registry_firstholycommunion` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `date_received` date NOT NULL, `priest` varchar(150) NOT NULL, `remarks` longtext NOT NULL, `member_id` bigint NOT NULL UNIQUE);
--
-- Create model LastRites
--
CREATE TABLE `registry_lastrites` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `date_administered` date NOT NULL, `priest` varchar(150) NOT NULL, `remarks` longtext NOT NULL, `member_id` bigint NOT NULL UNIQUE);
--
-- Create model Marriage
--
CREATE TABLE `registry_marriage` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `spouse_name` varchar(200) NOT NULL, `date_married` date NOT NULL, `priest` varchar(150) NOT NULL, `principal_sponsor` varchar(150) NOT NULL, `secondary_sponsor` varchar(150) NOT NULL, `remarks` longtext NOT NULL, `member_id` bigint NOT NULL);
--
-- Create model OrganizationMembership
--
CREATE TABLE `registry_organizationmembership` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `role` varchar(50) NOT NULL, `joined_date` date NOT NULL, `is_active` bool NOT NULL, `remarks` longtext NOT NULL, `date_created` date NOT NULL, `member_id` bigint NOT NULL, `organization_id` bigint NOT NULL);
--
-- Create model ParishOfficer
--
CREATE TABLE `registry_parishofficer` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `first_name` varchar(100) NOT NULL, `middle_name` varchar(100) NOT NULL, `last_name` varchar(100) NOT NULL, `position` varchar(150) NOT NULL, `contact_number` varchar(20) NOT NULL, `email` varchar(254) NOT NULL, `date_assigned` date NULL, `date_departed` date NULL, `status` varchar(10) NOT NULL, `biography` longtext NOT NULL, `remarks` longtext NOT NULL, `date_added` date NOT NULL, `date_updated` date NOT NULL, `image` varchar(100) NULL);
--
-- Create model ParishPriest
--
CREATE TABLE `registry_parishpriest` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `first_name` varchar(100) NOT NULL, `middle_name` varchar(100) NOT NULL, `last_name` varchar(100) NOT NULL, `contact_number` varchar(20) NOT NULL, `email` varchar(254) NOT NULL, `ordination_date` date NULL, `priest_since` date NULL, `date_assigned` date NULL, `date_departed` date NULL, `status` varchar(10) NOT NULL, `biography` longtext NOT NULL, `remarks` longtext NOT NULL, `date_added` date NOT NULL, `date_updated` date NOT NULL, `image` varchar(100) NULL, `user_id` integer NULL UNIQUE, `church_id` bigint NULL, `parish_id` bigint NULL);
--
-- Create model ParishOfficerEP
--
CREATE TABLE `registry_parishofficerep` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `first_name` varchar(100) NOT NULL, `middle_name` varchar(100) NOT NULL, `last_name` varchar(100) NOT NULL, `position` varchar(50) NOT NULL, `date_assigned` date NOT NULL, `date_departed` date NULL, `is_active` bool NOT NULL, `contact_number` varchar(20) NOT NULL, `email` varchar(254) NOT NULL, `remarks` longtext NOT NULL, `parish_id` bigint NOT NULL);
--
-- Create model Pledge
--
CREATE TABLE `registry_pledge` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `description` varchar(255) NOT NULL, `amount_pledged` numeric(10, 2) NOT NULL, `due_date` date NOT NULL, `status` varchar(10) NOT NULL, `date_created` date NOT NULL, `member_id` bigint NOT NULL);
--
-- Create model PledgePayment
--
CREATE TABLE `registry_pledgepayment` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `amount` numeric(10, 2) NOT NULL, `date_paid` date NOT NULL, `notes` varchar(255) NOT NULL, `status` varchar(10) NOT NULL, `submitted_by_member` bool NOT NULL, `pledge_id` bigint NOT NULL);
--
-- Create model Notification
--
CREATE TABLE `registry_notification` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `notification_type` varchar(20) NOT NULL, `title` varchar(200) NOT NULL, `message` longtext NOT NULL, `is_read` bool NOT NULL, `created_at` datetime(6) NOT NULL, `related_pledge_id` bigint NULL, `related_payment_id` bigint NULL, `user_id` integer NOT NULL);
--
-- Create model Donation
--
CREATE TABLE `registry_donation` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `description` varchar(255) NOT NULL, `amount` numeric(10, 2) NOT NULL, `date_donated` date NOT NULL, `date_created` date NOT NULL, `member_id` bigint NOT NULL);
--
-- Create model Offering
--
CREATE TABLE `registry_offering` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `description` varchar(255) NOT NULL, `total_amount` numeric(10, 2) NOT NULL, `date` date NOT NULL, `category` varchar(20) NOT NULL, `date_created` date NOT NULL, `member_id` bigint NOT NULL);
ALTER TABLE `registry_cathedral` ADD CONSTRAINT `registry_cathedral_church_id_55d6f985_fk_registry_church_id` FOREIGN KEY (`church_id`) REFERENCES `registry_church` (`id`);
ALTER TABLE `registry_parish` ADD CONSTRAINT `registry_parish_church_id_4486f7cf_fk_registry_church_id` FOREIGN KEY (`church_id`) REFERENCES `registry_church` (`id`);
ALTER TABLE `registry_member` ADD CONSTRAINT `registry_member_user_id_32452f2c_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `registry_member` ADD CONSTRAINT `registry_member_church_id_c77cbe45_fk_registry_church_id` FOREIGN KEY (`church_id`) REFERENCES `registry_church` (`id`);
ALTER TABLE `registry_member` ADD CONSTRAINT `registry_member_parish_id_4d819438_fk_registry_parish_id` FOREIGN KEY (`parish_id`) REFERENCES `registry_parish` (`id`);
ALTER TABLE `registry_baptism` ADD CONSTRAINT `registry_baptism_member_id_a76dfe2e_fk_registry_member_id` FOREIGN KEY (`member_id`) REFERENCES `registry_member` (`id`);
ALTER TABLE `registry_confirmation` ADD CONSTRAINT `registry_confirmation_member_id_69f34f15_fk_registry_member_id` FOREIGN KEY (`member_id`) REFERENCES `registry_member` (`id`);
ALTER TABLE `registry_firstholycommunion` ADD CONSTRAINT `registry_firstholyco_member_id_f67c8933_fk_registry_` FOREIGN KEY (`member_id`) REFERENCES `registry_member` (`id`);
ALTER TABLE `registry_lastrites` ADD CONSTRAINT `registry_lastrites_member_id_11c4be03_fk_registry_member_id` FOREIGN KEY (`member_id`) REFERENCES `registry_member` (`id`);
ALTER TABLE `registry_marriage` ADD CONSTRAINT `registry_marriage_member_id_ee682ac7_fk_registry_member_id` FOREIGN KEY (`member_id`) REFERENCES `registry_member` (`id`);
ALTER TABLE `registry_organizationmembership` ADD CONSTRAINT `registry_organizationmem_member_id_organization_i_b5a26e65_uniq` UNIQUE (`member_id`, `organization_id`);
ALTER TABLE `registry_organizationmembership` ADD CONSTRAINT `registry_organizatio_member_id_dc755e4c_fk_registry_` FOREIGN KEY (`member_id`) REFERENCES `registry_member` (`id`);
ALTER TABLE `registry_organizationmembership` ADD CONSTRAINT `registry_organizatio_organization_id_090dd1b4_fk_registry_` FOREIGN KEY (`organization_id`) REFERENCES `registry_organization` (`id`);
ALTER TABLE `registry_parishpriest` ADD CONSTRAINT `registry_parishpriest_user_id_0e8cac7e_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `registry_parishpriest` ADD CONSTRAINT `registry_parishpriest_church_id_8842a3bd_fk_registry_church_id` FOREIGN KEY (`church_id`) REFERENCES `registry_church` (`id`);
ALTER TABLE `registry_parishpriest` ADD CONSTRAINT `registry_parishpriest_parish_id_4c4cbb7d_fk_registry_parish_id` FOREIGN KEY (`parish_id`) REFERENCES `registry_parish` (`id`);
ALTER TABLE `registry_parishofficerep` ADD CONSTRAINT `registry_parishoffic_parish_id_9deacf62_fk_registry_` FOREIGN KEY (`parish_id`) REFERENCES `registry_parish` (`id`);
ALTER TABLE `registry_pledge` ADD CONSTRAINT `registry_pledge_member_id_c0383304_fk_registry_member_id` FOREIGN KEY (`member_id`) REFERENCES `registry_member` (`id`);
ALTER TABLE `registry_pledgepayment` ADD CONSTRAINT `registry_pledgepayment_pledge_id_ba5b6847_fk_registry_pledge_id` FOREIGN KEY (`pledge_id`) REFERENCES `registry_pledge` (`id`);
ALTER TABLE `registry_notification` ADD CONSTRAINT `registry_notificatio_related_pledge_id_f26b1fe4_fk_registry_` FOREIGN KEY (`related_pledge_id`) REFERENCES `registry_pledge` (`id`);
ALTER TABLE `registry_notification` ADD CONSTRAINT `registry_notificatio_related_payment_id_a73d7c52_fk_registry_` FOREIGN KEY (`related_payment_id`) REFERENCES `registry_pledgepayment` (`id`);
ALTER TABLE `registry_notification` ADD CONSTRAINT `registry_notification_user_id_a07cd5de_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `registry_donation` ADD CONSTRAINT `registry_donation_member_id_3562a204_fk_registry_member_id` FOREIGN KEY (`member_id`) REFERENCES `registry_member` (`id`);
ALTER TABLE `registry_offering` ADD CONSTRAINT `registry_offering_member_id_88b692ca_fk_registry_member_id` FOREIGN KEY (`member_id`) REFERENCES `registry_member` (`id`);
