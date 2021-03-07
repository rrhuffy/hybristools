START TRANSACTION;
UPDATE addresses SET p_dateofbirth=NOW(),
    p_firstname='FirstName',
    p_lastname='LastName',
    p_middlename='MiddleName',
    p_phone1='123456789',
    p_phone2='234567890',
    p_cellphone='345678901',
    p_email='anonymous@user.com',
    p_streetname='anonymousStreet',
    p_town='anonymousTown',
    p_postalcode='456789',
    p_streetnumber='12';
 
UPDATE emailaddress SET p_displayname='anonymousName',
    p_emailaddress=CONCAT('anonymous-',LEFT(UUID(),8),'@user.com');
 
UPDATE emailmessage SET p_replytoaddress='test@adress.com',
    p_subject='Anonymized subject',
    p_body='Ninja is hidden here';
 
UPDATE users SET uniqueID = CONCAT('UNIQUE-USER-',LEFT(UUID(),8)), 
    Name='AnonymousName',
    p_email='anonymous@user.com',
    p_phonenumber='789123456',
    passwd='nimda'
WHERE TypePkString = '8796094038098' AND pk != '8796093087748';
COMMIT;