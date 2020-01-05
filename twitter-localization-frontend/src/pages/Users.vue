<template>
    <div class="row">
      <div class="col-md-12">
        <card>
          <template slot="header">
            <h4 class="card-title">Located Users</h4>
            <p class="card-category">We have located over 500k users!</p>
            <table class="table table-hover">
              <thead>
                <th>Id</th>
                <th>Twitter Handle</th>
                <th>Estimated Location</th>
                <th>Confidence</th>
              </thead>
              <tbody>
              <tr>
                <td>jfchfgjsvh45f</td>
                <td><a href="/users?handle=lovehandle">@lovehandle</a> </td>
                <td>Bern, BE</td>
                <td>0.64</td>
              </tr>
              <tr>
                <td>fdhgsjkrwu45</td>
                <td><a href="/users?handle=RealDonaldTrump">@RealDonaldTrump</a></td>
                <td>R&uuml;ttihubelbad, BE</td>
                <td>0.91</td>
              </tr>
              <tr>
                <td>dvfdsjgi845</td>
                <td><a href="/users?handle=linusgsebastian">@linusgsebastian</a> </td>
                <td>Matzendorf, SO</td>
                <td>0.73</td>
              </tr>
              </tbody>
            </table>
          </template>
        </card>
      </div>

    </div>
</template>
<script>
export default {};
</script>
<style>
</style>
