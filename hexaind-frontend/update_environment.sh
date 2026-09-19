#!/bin/sh

FILE=$(ls /usr/share/nginx/html/main*.js)

[[ -z $HEXAIND_API_URL ]] || sed -i "s|apiUrl:\"[^,]*\"|apiUrl:\"${HEXAIND_API_URL}\"|g" $FILE
[[ -z $TDAM_API_URL ]] || sed -i "s|tdamUrl:\"[^,]*\"|tdamUrl:\"${TDAM_API_URL}\"|g" $FILE
[[ -z $HEXAIND_MB_API_URL ]] || sed -i "s|mbapiUrl:\"[^,]*\"|mbapiUrl:\"${HEXAIND_MB_API_URL}\"|g" $FILE
[[ -z $HEXAIND_DB_URL ]] || sed -i "s|dbUrl:\"[^,]*\"|dbUrl:\"${HEXAIND_DB_URL}\"}|g" $FILE
[[ -z $HEXAIND2_URL_EXT ]] || sed -i "s|hexaind2Urlext:\"[^,]*\"|hexaind2Urlext:\"${HEXAIND2_URL_EXT}\"|g" $FILE
[[ -z $HEXAIND3_URL_EXT ]] || sed -i "s|hexaind3Urlext:\"[^,]*\"|hexaind3Urlext:\"${HEXAIND3_URL_EXT}\"|g" $FILE
[[ -z $HEXAIND2_API_URL ]] || sed -i "s|hexaind2apiUrl:\"[^,]*\"|hexaind2apiUrl:\"${HEXAIND2_API_URL}\"|g" $FILE
[[ -z $HEXAIND_REDIRECT_URL ]] || sed -i "s|redirectUri:\"http://localhost:4200/\"|redirectUri:\"${HEXAIND_REDIRECT_URL}\"|g" $FILE
[[ -z $HEXAIND_REDIRECT_URL ]] || sed -i "s|redirectUri:\"http://localhost:4200/login\"|redirectUri:\"${HEXAIND_REDIRECT_URL}/login\"|g" $FILE
[[ -z $CLIENT_ID ]] || sed -i "s|clientId:\"[^,]*\"|clientId:\"$CLIENT_ID\"|g" $FILE
[[ -z $AUTHORITY ]] || sed -i "s|authority:\"[^,]*\"|authority:\"$AUTHORITY\"|g" $FILE
[[ -z $HEXAIND_AUX_API_URL ]] || sed -i "s|auxApiUrl:\"[^,]*\"|auxApiUrl:\"${HEXAIND_AUX_API_URL}\"|g" $FILE
