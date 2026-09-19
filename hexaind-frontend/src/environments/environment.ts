export const environment = {
  production: false,
  auxApiUrl: 'http://localhost:8000',
  apiUrl: 'http://localhost:8000',
  tdamUrl: 'http://172.31.128.55:8071',
  dbUrl: 'localhost:27017',
  clientId: '763bxaesxsatafb9-axasxysaxb37-4553-ay9sxassa62-a307f942a1ed',
  authority: 'f39qqqq6y221c-bdete8f-46asxdsax69-a89b-cb4fuawwe9a5eeeyb422',
  redirectUri: 'http://localhost:4200/',
  hexaind2apiUrl: 'https://hexaind3manualtest01be.corp.databrick.tech',
  hexaind2Urlext: 'https://hexaind2manualtest01.corp.databrick.tech',
  hexaind3Urlext: 'https://hexaind3manualtest01.corp.databrick.tech',
  mbapiUrl: 'http://localhost:8081',
};

export const authConfig = {
  production: false,
  authConfig: {
    issuer: 'https://accounts.google.com',
    clientId:
      '72102485asas9117-m0ejk8eaeaastaqsufdbgsaccla8c5tscm5feevwvdadddwdsa13kasasasasce7dki2a9mo64.apps.googleusercontent.com',
    redirectUri: 'http://localhost:4200/login',
    scope: 'openid profile email',
    responseType: 'token id_token',
    strictDiscoveryDocumentValidation: false,
    loginUrl: 'https://accounts.google.com/o/oauth2/v2/auth',
    tokenEndpoint: 'https://oauth2.googleapis.com/token',
    userinfoEndpoint: 'https://openidconnect.googleapis.com/v1/userinfo',
  },
};
